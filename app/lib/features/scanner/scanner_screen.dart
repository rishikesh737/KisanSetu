import 'dart:io';
import 'package:flutter/material.dart';
import 'package:file_picker/file_picker.dart';
import '../../services/disease_service.dart';

class ScannerScreen extends StatefulWidget {
  const ScannerScreen({super.key});

  @override
  State<ScannerScreen> createState() => _ScannerScreenState();
}

class _ScannerScreenState extends State<ScannerScreen> {
  final DiseaseService _diseaseService = DiseaseService();
  File? _selectedImage;
  String _resultText = 'Upload a leaf image for diagnosis.';
  bool _isLoading = false;

  Future<void> _pickAndDiagnoseImage() async {
    // 1. Pick the image file
    FilePickerResult? result = await FilePicker.pickFiles(
      type: FileType.image,
    );

    if (result != null && result.files.single.path != null) {
      setState(() {
        _selectedImage = File(result.files.single.path!);
        _isLoading = true;
        _resultText = 'Analyzing...';
      });

      try {
        // 2. Send to FastAPI backend
        final diagnosis = await _diseaseService.predictDisease(_selectedImage!);
        
        // 3. Update UI
        setState(() {
          _resultText = 'Diagnosis: ${diagnosis['disease_name']}\n'
                        'Confidence: ${(diagnosis['confidence'] * 100).toStringAsFixed(1)}%';
        });
      } catch (e) {
        setState(() {
          _resultText = 'Error: $e';
        });
      } finally {
        setState(() {
          _isLoading = false;
        });
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('KisanSetu AI Scanner'),
        backgroundColor: Colors.green[700],
        foregroundColor: Colors.white,
      ),
      body: Center(
        child: Padding(
          padding: const EdgeInsets.all(24.0),
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              // Image Preview Area
              Container(
                height: 300,
                width: double.infinity,
                decoration: BoxDecoration(
                  color: Colors.grey[200],
                  borderRadius: BorderRadius.circular(12),
                  border: Border.all(color: Colors.green),
                ),
                child: _selectedImage != null
                    ? ClipRRect(
                        borderRadius: BorderRadius.circular(12),
                        child: Image.file(_selectedImage!, fit: BoxFit.cover),
                      )
                    : const Icon(Icons.image, size: 100, color: Colors.grey),
              ),
              const SizedBox(height: 32),
              
              // Result Text
              if (_isLoading)
                const CircularProgressIndicator()
              else
                Text(
                  _resultText,
                  textAlign: TextAlign.center,
                  style: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
                ),
                
              const SizedBox(height: 32),
              
              // Upload Button
              ElevatedButton.icon(
                onPressed: _isLoading ? null : _pickAndDiagnoseImage,
                icon: const Icon(Icons.upload_file),
                label: const Text('Upload Leaf Image'),
                style: ElevatedButton.styleFrom(
                  backgroundColor: Colors.green[700],
                  foregroundColor: Colors.white,
                  padding: const EdgeInsets.symmetric(horizontal: 32, vertical: 16),
                  textStyle: const TextStyle(fontSize: 18),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
