import 'dart:io';
import 'package:flutter/services.dart' show rootBundle;
import 'package:tflite_flutter/tflite_flutter.dart';
import 'package:image/image.dart' as img;

// ─── Weather Data Model ────────────────────────────────────────────────────
/// Cached local weather conditions used as an environmental prior
/// to adjust raw model probabilities.
///
/// TODO: Replace dummy values with real cached weather data from
/// the backend Weather API once the weather feature screen is built.
class WeatherData {
  final double temperature; // °C
  final double humidity;    // % (0-100)
  final double rainfall;   // mm (recent/daily)

  const WeatherData({
    required this.temperature,
    required this.humidity,
    required this.rainfall,
  });

  /// Dummy cached weather for development/testing.
  /// Simulates a typical Goa/Maharashtra monsoon day.
  static const WeatherData defaultCached = WeatherData(
    temperature: 28.0,
    humidity: 88.0,
    rainfall: 60.0,
  );
}

// ─── Disease Service ───────────────────────────────────────────────────────
/// Offline rice disease classifier using TFLite on-device inference
/// with weather-based environmental prior adjustment.
///
/// Model: MobileNetV2 fine-tuned on 5 rice disease classes.
/// Input: 224x224 RGB image, raw [0,255] pixels (normalization baked in).
/// Output: 5-element softmax probability vector.
///
/// Class indices (alphabetical, matching TensorFlow's folder ordering):
///   0: Rice_Bacterial_Blight
///   1: Rice_Blast
///   2: Rice_Brown_Spot
///   3: Rice_Healthy
///   4: Rice_Tungro
class DiseaseService {
  static const String _modelPath = 'assets/models/rice_expert_v1.tflite';
  static const String _labelsPath = 'assets/labels/rice_labels.txt';
  static const int _inputSize = 224;
  static const double _confidenceThreshold = 0.85; // 85%

  // Weather Fusion multiplier constants
  static const double _humidityBoostThreshold = 85.0;
  static const double _rainfallBoostThreshold = 50.0;
  static const double _dryHumidityThreshold = 65.0;
  static const double _dryRainfallThreshold = 10.0;
  static const double _blastHumidityMultiplier = 1.3;
  static const double _blightRainfallMultiplier = 1.3;
  static const double _brownSpotDryMultiplier = 1.4;

  // Class indices (alphabetical order)
  static const int _idxBacterialBlight = 0;
  static const int _idxBlast = 1;
  static const int _idxBrownSpot = 2;
  // static const int _idxHealthy = 3;
  // static const int _idxTungro = 4;

  Interpreter? _interpreter;
  List<String> _labels = [];
  bool _isInitialized = false;

  /// Initialize the TFLite interpreter and load labels.
  /// Call once at app startup or before first scan.
  Future<void> initialize() async {
    if (_isInitialized) return;

    // Load TFLite model from bundled assets
    _interpreter = await Interpreter.fromAsset(_modelPath);

    // Load class labels (one per line)
    final labelData = await rootBundle.loadString(_labelsPath);
    _labels = labelData.trim().split('\n');

    _isInitialized = true;
  }

  /// Classify a rice leaf image from a [File].
  ///
  /// Performs:
  /// 1. Image decode + resize to 224x224
  /// 2. TFLite inference (raw [0,255] pixels — model handles normalization)
  /// 3. Weather Fusion: adjusts probabilities using environmental priors
  /// 4. Re-normalization so adjusted probabilities sum to 1.0
  ///
  /// Returns a map with:
  ///   - `disease_name`: Human-readable disease name
  ///   - `confidence`: Weather-adjusted probability as percentage (0-100)
  ///   - `is_confident`: Whether confidence meets the 85% threshold
  ///   - `all_predictions`: Full sorted list of predictions
  ///   - `weather_adjusted`: Whether weather fusion was applied
  Future<Map<String, dynamic>> classifyImage(
    File imageFile, {
    WeatherData weather = WeatherData.defaultCached,
  }) async {
    if (!_isInitialized) await initialize();

    // ── Step 1: Decode and resize image to 224x224 ──────────────────────
    final bytes = await imageFile.readAsBytes();
    img.Image? rawImage = img.decodeImage(bytes);
    if (rawImage == null) {
      throw Exception('Failed to decode image.');
    }
    final resized = img.copyResize(
      rawImage,
      width: _inputSize,
      height: _inputSize,
    );

    // ── Step 2: Convert to input tensor [1, 224, 224, 3] as Float32 ─────
    // Feed raw [0, 255] values — the model's Rescaling layer normalizes internally
    var input = List.generate(
      1,
      (_) => List.generate(
        _inputSize,
        (y) => List.generate(
          _inputSize,
          (x) {
            final pixel = resized.getPixel(x, y);
            return [
              pixel.r.toDouble(),
              pixel.g.toDouble(),
              pixel.b.toDouble(),
            ];
          },
        ),
      ),
    );

    // ── Step 3: Prepare output buffer [1, numClasses] ───────────────────
    var output = List.generate(1, (_) => List.filled(_labels.length, 0.0));

    // ── Step 4: Run TFLite inference ────────────────────────────────────
    _interpreter!.run(input, output);

    // ── Step 5: Weather Fusion — Apply environmental priors ─────────────
    List<double> probabilities = List<double>.from(output[0]);
    bool weatherAdjusted = false;

    // Rice Blast (index 1): thrives in high humidity
    if (weather.humidity > _humidityBoostThreshold) {
      probabilities[_idxBlast] *= _blastHumidityMultiplier;
      weatherAdjusted = true;
    }

    // Bacterial Blight (index 0): driven by heavy rainfall/monsoons
    if (weather.rainfall > _rainfallBoostThreshold) {
      probabilities[_idxBacterialBlight] *= _blightRainfallMultiplier;
      weatherAdjusted = true;
    }

    // Brown Spot (index 2): appears in drier conditions
    if (weather.humidity < _dryHumidityThreshold &&
        weather.rainfall < _dryRainfallThreshold) {
      probabilities[_idxBrownSpot] *= _brownSpotDryMultiplier;
      weatherAdjusted = true;
    }

    // ── Step 6: Re-normalize so probabilities sum to 1.0 ───────────────
    if (weatherAdjusted) {
      final sum = probabilities.reduce((a, b) => a + b);
      if (sum > 0) {
        for (int i = 0; i < probabilities.length; i++) {
          probabilities[i] /= sum;
        }
      }
    }

    // ── Step 7: Parse results ──────────────────────────────────────────
    double maxConfidence = 0.0;
    int predictedIndex = 0;
    for (int i = 0; i < probabilities.length; i++) {
      if (probabilities[i] > maxConfidence) {
        maxConfidence = probabilities[i];
        predictedIndex = i;
      }
    }

    final confidencePercent = maxConfidence * 100;

    // Build sorted predictions list
    List<Map<String, dynamic>> allPredictions = [];
    for (int i = 0; i < _labels.length; i++) {
      allPredictions.add({
        'disease_name': _labels[i].replaceAll('_', ' '),
        'confidence': (probabilities[i] * 100).toStringAsFixed(1),
      });
    }
    allPredictions.sort((a, b) =>
        double.parse(b['confidence']).compareTo(double.parse(a['confidence'])));

    return {
      'disease_name': _labels[predictedIndex].replaceAll('_', ' '),
      'confidence': confidencePercent,
      'is_confident': confidencePercent >= (_confidenceThreshold * 100),
      'all_predictions': allPredictions,
      'weather_adjusted': weatherAdjusted,
    };
  }

  /// Release interpreter resources.
  void dispose() {
    _interpreter?.close();
    _isInitialized = false;
  }
}
