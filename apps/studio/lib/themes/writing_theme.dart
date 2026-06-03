import 'package:flutter/material.dart';

class WritingColors {
  static const bg = Color(0xFF1a1b1e);
  static const surface = Color(0xFF25262b);
  static const surface2 = Color(0xFF2c2e33);
  static const border = Color(0xFF373a40);
  static const text = Color(0xFFc1c2c5);
  static const textDim = Color(0xFF909296);
  static const accent = Color(0xFF7c9bff);
  static const accent2 = Color(0xFF69db7c);
  static const accent3 = Color(0xFFffd43b);
  static const red = Color(0xFFff6b6b);
}

class WritingTheme {
  static ThemeData get dark {
    return ThemeData(
      useMaterial3: true,
      brightness: Brightness.dark,
      scaffoldBackgroundColor: WritingColors.bg,
      colorScheme: ColorScheme.dark(
        surface: WritingColors.bg,
        primary: WritingColors.accent,
        secondary: WritingColors.accent2,
        tertiary: WritingColors.accent3,
        error: WritingColors.red,
        onSurface: WritingColors.text,
        onSurfaceVariant: WritingColors.textDim,
        outline: WritingColors.border,
      ),
      appBarTheme: const AppBarTheme(
        backgroundColor: WritingColors.surface,
        foregroundColor: WritingColors.text,
        elevation: 0,
        scrolledUnderElevation: 0,
      ),
      textTheme: const TextTheme(
        bodySmall: TextStyle(color: WritingColors.textDim, fontSize: 11),
        bodyMedium: TextStyle(color: WritingColors.text, fontSize: 13),
        bodyLarge: TextStyle(color: WritingColors.text, fontSize: 15),
      ),
      dividerTheme: const DividerThemeData(color: WritingColors.border, thickness: 1),
    );
  }
}
