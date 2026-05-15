import 'package:flutter/material.dart';

class AuthService extends ChangeNotifier {
  // Singleton pattern for easy access
  static final AuthService _instance = AuthService._internal();
  factory AuthService() => _instance;
  AuthService._internal();

  bool _isLoggedIn = false;
  bool get isLoggedIn => _isLoggedIn;

  String _userName = "Rishikesh Pednekar";
  String get userName => _userName;

  String _phoneNumber = "+91 98765 43210";
  String get phoneNumber => _phoneNumber;

  String _locationName = "Pune, Maharashtra";
  String get locationName => _locationName;

  double? _latitude;
  double? get latitude => _latitude;

  double? _longitude;
  double? get longitude => _longitude;

  void login({String? name}) {
    if (name != null) _userName = name;
    _isLoggedIn = true;
    notifyListeners();
  }

  void signup({required String name, required String phone}) {
    _userName = name;
    _phoneNumber = phone;
    _isLoggedIn = true;
    notifyListeners();
  }

  void logout() {
    _isLoggedIn = false;
    notifyListeners();
  }

  void updateLocation(String name, {double? lat, double? lng}) {
    _locationName = name;
    _latitude = lat;
    _longitude = lng;
    notifyListeners();
  }

  void updateProfile({String? name, String? phone}) {
    if (name != null) _userName = name;
    if (phone != null) _phoneNumber = phone;
    notifyListeners();
  }
}
