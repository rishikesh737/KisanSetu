import 'package:flutter/material.dart';
import 'features/scanner/scanner_screen.dart';

void main() {
  runApp(const KisanSetuApp());
}

class KisanSetuApp extends StatelessWidget {
  const KisanSetuApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'KisanSetu',
      theme: ThemeData(
        colorScheme: ColorScheme.fromSeed(seedColor: Colors.green),
        useMaterial3: true,
      ),
      home: const ScannerScreen(), // This tells the app to load your new scanner!
    );
  }
}
