import 'package:flutter/material.dart';

enum Language { english, hindi, marathi }

class TranslationService extends ChangeNotifier {
  static final TranslationService _instance = TranslationService._internal();
  factory TranslationService() => _instance;
  TranslationService._internal();

  Language _currentLanguage = Language.english;
  Language get currentLanguage => _currentLanguage;

  void setLanguage(Language language) {
    _currentLanguage = language;
    notifyListeners();
  }

  static const Map<String, Map<Language, String>> _translations = {
    'home': {
      Language.english: 'Home',
      Language.hindi: 'मुख्य',
      Language.marathi: 'मुख्य',
    },
    'scan': {
      Language.english: 'Scan',
      Language.hindi: 'स्कॅन',
      Language.marathi: 'स्कॅन',
    },
    'reports': {
      Language.english: 'Reports',
      Language.hindi: 'रिपोर्ट्स',
      Language.marathi: 'अहवाल',
    },
    'profile': {
      Language.english: 'Profile',
      Language.hindi: 'प्रोफ़ाइल',
      Language.marathi: 'प्रोफाइल',
    },
    'greeting': {
      Language.english: 'नमस्ते',
      Language.hindi: 'नमस्ते',
      Language.marathi: 'नमस्कार',
    },
    'scan_crop': {
      Language.english: 'Scan Crop',
      Language.hindi: 'फसल को स्कॅन करें',
      Language.marathi: 'पीक स्कॅन करा',
    },
    'mandi_prices': {
      Language.english: 'Mandi Prices',
      Language.hindi: 'मंडी भाव',
      Language.marathi: 'मंडीचे भाव',
    },
    'quick_actions': {
      Language.english: 'Quick Actions',
      Language.hindi: 'त्वरित क्रियाएं',
      Language.marathi: 'त्वरित कृती',
    },
    'recent_scans': {
      Language.english: 'Recent Scans',
      Language.hindi: 'हाल के स्कॅन',
      Language.marathi: 'अलीकडील स्कॅन',
    },
    'expert_advice': {
      Language.english: 'Expert Advice',
      Language.hindi: 'विशेषज्ञ सलाह',
      Language.marathi: 'तज्ज्ञांचा सल्ला',
    },
    'view_all': {
      Language.english: 'View All',
      Language.hindi: 'सभी देखें',
      Language.marathi: 'सर्व पहा',
    },
    'change_location': {
      Language.english: 'Change Location',
      Language.hindi: 'स्थान बदलें',
      Language.marathi: 'ठिकाण बदला',
    },
    'language': {
      Language.english: 'Language',
      Language.hindi: 'भाषा',
      Language.marathi: 'भाषा',
    },
    'logout': {
      Language.english: 'Logout',
      Language.hindi: 'लॉग आउट',
      Language.marathi: 'लॉग आउट',
    },
  };

  String translate(String key) {
    if (!_translations.containsKey(key)) return key;
    return _translations[key]![_currentLanguage] ?? key;
  }
}

extension TranslationExtension on String {
  String get tr => TranslationService().translate(this);
}
