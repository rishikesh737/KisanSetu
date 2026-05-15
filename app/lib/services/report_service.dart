import 'package:flutter/material.dart';

class ScanResult {
  final String disease;
  final String date;
  final String status;
  final Color statusColor;

  ScanResult({
    required this.disease,
    required this.date,
    required this.status,
    required this.statusColor,
  });
}

class ReportService extends ChangeNotifier {
  static final ReportService _instance = ReportService._internal();
  factory ReportService() => _instance;
  ReportService._internal();

  final List<ScanResult> _history = [
    ScanResult(disease: 'Leaf Blast', date: 'Today, 09:41 AM', status: 'Confirmed', statusColor: Colors.orange),
    ScanResult(disease: 'Healthy Crop', date: 'Yesterday, 14:20 PM', status: 'All Good', statusColor: Colors.green),
    ScanResult(disease: 'Brown Spot', date: '12 May, 08:15 AM', status: 'Resolved', statusColor: Colors.grey),
  ];

  List<ScanResult> get history => _history;

  void addResult(ScanResult result) {
    _history.insert(0, result);
    notifyListeners();
  }
}
