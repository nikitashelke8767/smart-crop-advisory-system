import 'package:flutter/material.dart';

class CustomCard extends StatelessWidget {
  final String title;
  final String content;

  const CustomCard({super.key, required this.title, required this.content});

  @override
  Widget build(BuildContext context) {
    return Card(
      child: ListTile(
        title: Text(title),
        subtitle: Text(content),
      ),
    );
  }
}
