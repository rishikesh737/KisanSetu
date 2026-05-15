import 'dart:io';
import 'package:flutter/material.dart';
import 'package:file_picker/file_picker.dart';
import '../services/disease_service.dart';
import '../services/navigation_service.dart';
import '../services/report_service.dart';
import '../services/translation_service.dart';

class DiseaseDetectionScreen extends StatefulWidget {
  const DiseaseDetectionScreen({super.key});

  @override
  State<DiseaseDetectionScreen> createState() => _DiseaseDetectionScreenState();
}

class _DiseaseDetectionScreenState extends State<DiseaseDetectionScreen> with SingleTickerProviderStateMixin {
  final DiseaseService _diseaseService = DiseaseService();
  File? _selectedImage;
  bool _isLoading = false;
  Map<String, dynamic>? _result;
  late AnimationController _pulseController;

  @override
  void initState() {
    super.initState();
    _pulseController = AnimationController(
      vsync: this,
      duration: const Duration(seconds: 2),
    )..repeat(reverse: true);
  }

  @override
  void dispose() {
    _diseaseService.dispose();
    _pulseController.dispose();
    super.dispose();
  }

  Future<void> _pickAndDiagnoseImage() async {
    FilePickerResult? result = await FilePicker.pickFiles(
      type: FileType.image,
    );

    if (result != null && result.files.single.path != null) {
      setState(() {
        _selectedImage = File(result.files.single.path!);
        _isLoading = true;
        _result = null;
      });

      try {
        final prediction = await _diseaseService.classifyImage(_selectedImage!);
        setState(() {
          _result = prediction;
        });

        // Save to report service
        final String diseaseName = prediction['disease_name'] ?? 'Unknown';
        final bool isConfident = prediction['is_confident'] ?? false;
        
        ReportService().addResult(ScanResult(
          disease: isConfident ? diseaseName : 'scan_unclear'.tr,
          date: 'just_now'.tr,
          status: isConfident ? 'confirmed'.tr : 'unclear'.tr,
          statusColor: isConfident ? Colors.green : Colors.orange,
        ));

      } catch (e) {
        setState(() {
          _result = {'error': e.toString()};
        });
      } finally {
        setState(() {
          _isLoading = false;
        });
      }
    }
  }

  void _reset() {
    setState(() {
      _selectedImage = null;
      _result = null;
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFFF7FBF7),
      appBar: AppBar(
        title: Text('scan'.tr, style: const TextStyle(fontWeight: FontWeight.bold)),
        backgroundColor: Colors.transparent,
        elevation: 0,
        foregroundColor: Colors.green[900],
        centerTitle: true,
      ),
      body: SafeArea(
        child: Padding(
          padding: const EdgeInsets.all(24.0),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              if (_selectedImage == null) ...[
                const Spacer(),
                _buildUploadPrompt(),
                const Spacer(),
                _buildUploadButton(),
              ] else if (_isLoading) ...[
                const Spacer(),
                _buildLoadingSpinner(),
                const Spacer(),
              ] else if (_result != null) ...[
                _buildResultView(),
                const Spacer(),
                _buildActionButtons(),
              ],
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildUploadPrompt() {
    return Column(
      children: [
        Container(
          width: 160,
          height: 160,
          decoration: BoxDecoration(
            color: const Color(0xFFE8F5E9),
            shape: BoxShape.circle,
            boxShadow: [
              BoxShadow(
                color: Colors.green.withOpacity(0.1),
                blurRadius: 30,
                spreadRadius: 10,
              )
            ],
          ),
          child: Icon(Icons.document_scanner_outlined, size: 80, color: Colors.green[700]),
        ),
        const SizedBox(height: 32),
        Text(
          'scan_your_crop'.tr.isEmpty ? 'Scan Your Crop' : 'scan_your_crop'.tr,
          style: TextStyle(fontSize: 24, fontWeight: FontWeight.bold, color: Colors.green[900]),
        ),
        const SizedBox(height: 12),
        Text(
          'upload_instruction'.tr.isEmpty ? 'Upload a clear image of the affected rice leaf for an instant AI diagnosis.' : 'upload_instruction'.tr,
          textAlign: TextAlign.center,
          style: TextStyle(fontSize: 16, color: Colors.grey[600]),
        ),
      ],
    );
  }

  Widget _buildUploadButton() {
    return Container(
      decoration: BoxDecoration(
        gradient: const LinearGradient(
          colors: [Color(0xFF81C784), Color(0xFF4CAF50)],
        ),
        borderRadius: BorderRadius.circular(16),
        boxShadow: [
          BoxShadow(
            color: Colors.green.withOpacity(0.3),
            blurRadius: 15,
            offset: const Offset(0, 8),
          ),
        ],
      ),
      child: ElevatedButton(
        onPressed: _pickAndDiagnoseImage,
        style: ElevatedButton.styleFrom(
          backgroundColor: Colors.transparent,
          shadowColor: Colors.transparent,
          padding: const EdgeInsets.symmetric(vertical: 20),
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
        ),
        child: Text(
          'select_image'.tr.isEmpty ? 'Select Image' : 'select_image'.tr,
          style: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold, color: Colors.white),
        ),
      ),
    );
  }

  Widget _buildLoadingSpinner() {
    return Column(
      children: [
        AnimatedBuilder(
          animation: _pulseController,
          builder: (context, child) {
            return Transform.scale(
              scale: 1.0 + (_pulseController.value * 0.1),
              child: Container(
                width: 150,
                height: 150,
                decoration: BoxDecoration(
                  shape: BoxShape.circle,
                  gradient: RadialGradient(
                    colors: [
                      Colors.green[200]!.withOpacity(0.8),
                      Colors.green[50]!.withOpacity(0.1),
                    ],
                  ),
                ),
                child: Padding(
                  padding: const EdgeInsets.all(20.0),
                  child: ClipOval(
                    child: Image.file(_selectedImage!, fit: BoxFit.cover),
                  ),
                ),
              ),
            );
          },
        ),
        const SizedBox(height: 32),
        Text(
          'analysis_progress'.tr.isEmpty ? 'Analysis in progress...' : 'analysis_progress'.tr,
          style: const TextStyle(fontSize: 20, fontWeight: FontWeight.bold, color: Colors.green),
        ),
        const SizedBox(height: 8),
        Text(
          'Identifying pathogens and assessing severity',
          style: TextStyle(fontSize: 14, color: Colors.grey[600]),
        ),
      ],
    );
  }

  Widget _buildResultView() {
    bool isError = _result!.containsKey('error');
    if (isError) {
      return Center(
        child: Text('Error: ${_result!['error']}', style: const TextStyle(color: Colors.red)),
      );
    }

    double confidence = _result!['confidence'] ?? 0.0;
    String diseaseName = _result!['disease_name'] ?? 'Unknown';
    bool isConfident = _result!['is_confident'] ?? false;
    bool weatherAdjusted = _result!['weather_adjusted'] ?? false;

    return Column(
      children: [
        ClipRRect(
          borderRadius: BorderRadius.circular(20),
          child: Image.file(_selectedImage!, height: 250, width: double.infinity, fit: BoxFit.cover),
        ),
        const SizedBox(height: 24),
        Container(
          padding: const EdgeInsets.all(24),
          decoration: BoxDecoration(
            color: Colors.white,
            borderRadius: BorderRadius.circular(24),
            boxShadow: [
              BoxShadow(
                color: Colors.black.withOpacity(0.05),
                blurRadius: 20,
                offset: const Offset(0, 10),
              )
            ],
          ),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  Text(
                    'diagnosis_result'.tr.isEmpty ? 'Diagnosis Result' : 'diagnosis_result'.tr,
                    style: TextStyle(fontSize: 14, color: Colors.grey[500], fontWeight: FontWeight.w600),
                  ),
                  if (weatherAdjusted)
                    Row(
                      children: [
                        Icon(Icons.wb_cloudy_outlined, size: 14, color: Colors.blue[400]),
                        const SizedBox(width: 4),
                        Text('Weather Prior', style: TextStyle(fontSize: 12, color: Colors.blue[400])),
                      ],
                    ),
                ],
              ),
              const SizedBox(height: 8),
              Text(
                isConfident ? diseaseName : 'scan_unclear'.tr,
                style: TextStyle(
                  fontSize: 24, 
                  fontWeight: FontWeight.bold, 
                  color: isConfident ? Colors.green[900] : Colors.orange[800]
                ),
              ),
              const SizedBox(height: 16),
              LinearProgressIndicator(
                value: confidence / 100,
                backgroundColor: Colors.grey[200],
                valueColor: AlwaysStoppedAnimation<Color>(
                  isConfident ? Colors.green : Colors.orange,
                ),
                minHeight: 8,
                borderRadius: BorderRadius.circular(4),
              ),
              const SizedBox(height: 8),
              Text(
                '${confidence.toStringAsFixed(1)}% Confidence',
                style: TextStyle(fontSize: 14, color: Colors.grey[700]),
              ),
              if (!isConfident) ...[
                const SizedBox(height: 12),
                Text(
                  'This may not be a recognized rice disease. Please ensure you are scanning a rice leaf.',
                  style: TextStyle(fontSize: 13, color: Colors.orange[800]),
                ),
              ]
            ],
          ),
        ),
      ],
    );
  }

  Widget _buildActionButtons() {
    return Column(
      children: [
        OutlinedButton(
          onPressed: () {
            NavigationService().changeIndex(2);
          },
          style: OutlinedButton.styleFrom(
            side: BorderSide(color: Colors.green[700]!),
            padding: const EdgeInsets.symmetric(vertical: 16),
            shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
            minimumSize: const Size(double.infinity, 50),
          ),
          child: Text(
            'view_full_report'.tr.isEmpty ? 'View Full Report' : 'view_full_report'.tr,
            style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold, color: Colors.green[700]),
          ),
        ),
        const SizedBox(height: 16),
        TextButton(
          onPressed: _reset,
          child: Text('scan_another'.tr.isEmpty ? 'Scan Another Image' : 'scan_another'.tr, style: const TextStyle(fontSize: 16, color: Colors.grey)),
        ),
      ],
    );
  }
}
