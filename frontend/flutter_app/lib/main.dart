import 'package:flutter/material.dart';

void main() {
  runApp(const SmartCropApp());
}

class SmartCropApp extends StatelessWidget {
  const SmartCropApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Smart Crop Advisory',
      theme: ThemeData(primarySwatch: Colors.green),
      home: const Scaffold(body: Center(child: Text('Smart Crop Advisory App'))),
    );
  }
}
