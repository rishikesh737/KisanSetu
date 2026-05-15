import 'package:flutter/material.dart';
import '../services/translation_service.dart';

class LanguageSelectionScreen extends StatelessWidget {
  const LanguageSelectionScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFFF7FBF7),
      body: SafeArea(
        child: Padding(
          padding: const EdgeInsets.symmetric(horizontal: 24.0, vertical: 48.0),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              Text(
                'Select Your Language',
                textAlign: TextAlign.center,
                style: TextStyle(
                  fontSize: 28,
                  fontWeight: FontWeight.bold,
                  color: Colors.green[900],
                ),
              ),
              const SizedBox(height: 12),
              Text(
                'अपनी भाषा चुनें / तुमची भाषा निवडा',
                textAlign: TextAlign.center,
                style: TextStyle(
                  fontSize: 16,
                  color: Colors.grey[600],
                ),
              ),
              const SizedBox(height: 48),
              _buildLanguageCard(context, 'English', 'English', Language.english),
              const SizedBox(height: 16),
              _buildLanguageCard(context, 'हिंदी', 'Hindi', Language.hindi),
              const SizedBox(height: 16),
              _buildLanguageCard(context, 'मराठी', 'Marathi', Language.marathi),
              const Spacer(),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildLanguageCard(BuildContext context, String nativeName, String engName, Language lang) {
    return GestureDetector(
      onTap: () {
        TranslationService().setLanguage(lang);
        Navigator.pop(context);
      },
      child: Container(
        padding: const EdgeInsets.all(24),
        decoration: BoxDecoration(
          color: Colors.white,
          borderRadius: BorderRadius.circular(20),
          boxShadow: [
            BoxShadow(
              color: Colors.black.withOpacity(0.02),
              blurRadius: 10,
              offset: const Offset(0, 4),
            ),
          ],
        ),
        child: Row(
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: [
            Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  nativeName,
                  style: TextStyle(
                    fontSize: 20,
                    fontWeight: FontWeight.bold,
                    color: Colors.green[900],
                  ),
                ),
                Text(
                  engName,
                  style: TextStyle(
                    fontSize: 14,
                    color: Colors.grey[500],
                  ),
                ),
              ],
            ),
            Icon(Icons.arrow_forward_ios, color: Colors.green[700], size: 16),
          ],
        ),
      ),
    );
  }
}
