import 'dart:convert';
import 'dart:io';
import 'package:http/http.dart' as http;
import 'package:http_parser/http_parser.dart'; // <-- Required for MediaType

class DiseaseService {
  // If running on a physical device or emulator, use your machine's IP.
  // If running as a Linux desktop app locally, localhost is fine.
  static const String _baseUrl = 'http://127.0.0.1:8000/api/v1/disease';

  /// Sends a crop image to the backend and returns the prediction.
  Future<Map<String, dynamic>> predictDisease(File imageFile) async {
    try {
      var request = http.MultipartRequest(
        'POST',
        Uri.parse('$_baseUrl/predict'),
      );

      // Determine the extension (e.g., 'jpg', 'png')
      String extension = imageFile.path.split('.').last.toLowerCase();
      if (extension == 'jpg') extension = 'jpeg';

      // Attach the image file to the request WITH a content type
      request.files.add(
        await http.MultipartFile.fromPath(
          'file',
          imageFile.path,
          contentType: MediaType('image', extension), // <-- Tells FastAPI it's an image
        ),
      );

      // Send the request
      var response = await request.send();

      if (response.statusCode == 200) {
        // Parse the stream into a String, then into a JSON map
        var responseData = await response.stream.bytesToString();
        var decodedData = json.decode(responseData);
        return decodedData;
      } else {
        // Capture the actual error message from the backend if possible
        var errorData = await response.stream.bytesToString();
        throw Exception('Failed to diagnose crop. Status: ${response.statusCode}, Body: $errorData');
      }
    } catch (e) {
      throw Exception('Network error during prediction: $e');
    }
  }
}
