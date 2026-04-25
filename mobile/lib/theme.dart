import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';

// ── Paleta de colores Medix AI ──────────────────────────────────
class MedixColors {
  // Primarios
  static const blue = Color(0xFF0A84FF);
  static const blueDark = Color(0xFF0060C7);
  static const blueLight = Color(0xFF3FA3FF);

  // Fondos (dark theme)
  static const bgPrimary = Color(0xFF0F172A);    // Fondo principal
  static const bgSurface = Color(0xFF1E293B);    // Cards, modales
  static const bgElevated = Color(0xFF2D3748);   // Hover, active

  // Estado / semáforo médico
  static const success = Color(0xFF22C55E);      // Verde — ok
  static const warning = Color(0xFFF59E0B);      // Ámbar — precaución
  static const danger = Color(0xFFEF4444);       // Rojo — urgente
  static const critical = Color(0xFFDC2626);     // Rojo oscuro — crítico

  // Texto
  static const textPrimary = Color(0xFFF8FAFC);
  static const textSecondary = Color(0xFF94A3B8);
  static const textMuted = Color(0xFF475569);

  // Bordes
  static const border = Color(0xFF334155);
  static const borderLight = Color(0xFF475569);
}

// ── Tema principal Medix AI ─────────────────────────────────────
class MedixTheme {
  static ThemeData get dark {
    return ThemeData(
      useMaterial3: true,
      brightness: Brightness.dark,
      scaffoldBackgroundColor: MedixColors.bgPrimary,
      colorScheme: const ColorScheme.dark(
        primary: MedixColors.blue,
        secondary: MedixColors.success,
        surface: MedixColors.bgSurface,
        error: MedixColors.danger,
        onPrimary: Colors.white,
        onSurface: MedixColors.textPrimary,
      ),
      textTheme: GoogleFonts.plusJakartaSansTextTheme(
        ThemeData.dark().textTheme,
      ).copyWith(
        displayLarge: GoogleFonts.plusJakartaSans(
          fontSize: 32, fontWeight: FontWeight.w700, color: MedixColors.textPrimary,
        ),
        headlineMedium: GoogleFonts.plusJakartaSans(
          fontSize: 22, fontWeight: FontWeight.w600, color: MedixColors.textPrimary,
        ),
        titleMedium: GoogleFonts.plusJakartaSans(
          fontSize: 16, fontWeight: FontWeight.w500, color: MedixColors.textPrimary,
        ),
        bodyMedium: GoogleFonts.plusJakartaSans(
          fontSize: 14, color: MedixColors.textSecondary,
        ),
      ),
      cardTheme: CardThemeData(
        color: MedixColors.bgSurface,
        elevation: 0,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(16),
          side: const BorderSide(color: MedixColors.border, width: 1),
        ),
      ),
      elevatedButtonTheme: ElevatedButtonThemeData(
        style: ElevatedButton.styleFrom(
          backgroundColor: MedixColors.blue,
          foregroundColor: Colors.white,
          minimumSize: const Size(double.infinity, 52),
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
          textStyle: GoogleFonts.plusJakartaSans(
            fontSize: 15, fontWeight: FontWeight.w600,
          ),
        ),
      ),
      inputDecorationTheme: InputDecorationTheme(
        filled: true,
        fillColor: MedixColors.bgSurface,
        border: OutlineInputBorder(
          borderRadius: BorderRadius.circular(12),
          borderSide: const BorderSide(color: MedixColors.border),
        ),
        enabledBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(12),
          borderSide: const BorderSide(color: MedixColors.border),
        ),
        focusedBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(12),
          borderSide: const BorderSide(color: MedixColors.blue, width: 2),
        ),
        labelStyle: const TextStyle(color: MedixColors.textSecondary),
        hintStyle: const TextStyle(color: MedixColors.textMuted),
      ),
      appBarTheme: const AppBarTheme(
        backgroundColor: MedixColors.bgPrimary,
        elevation: 0,
        surfaceTintColor: Colors.transparent,
        titleTextStyle: TextStyle(
          color: MedixColors.textPrimary,
          fontSize: 18,
          fontWeight: FontWeight.w600,
        ),
        iconTheme: IconThemeData(color: MedixColors.textPrimary),
      ),
      bottomNavigationBarTheme: const BottomNavigationBarThemeData(
        backgroundColor: MedixColors.bgSurface,
        selectedItemColor: MedixColors.blue,
        unselectedItemColor: MedixColors.textMuted,
        type: BottomNavigationBarType.fixed,
        elevation: 0,
      ),
      dividerTheme: const DividerThemeData(color: MedixColors.border, thickness: 1),
    );
  }
}

// ── Widgets reutilizables Medix ────────────────────────────────
class MedixCard extends StatelessWidget {
  final Widget child;
  final EdgeInsets? padding;
  final Color? color;
  final VoidCallback? onTap;

  const MedixCard({super.key, required this.child, this.padding, this.color, this.onTap});

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onTap,
      child: Container(
        padding: padding ?? const EdgeInsets.all(16),
        decoration: BoxDecoration(
          color: color ?? MedixColors.bgSurface,
          borderRadius: BorderRadius.circular(16),
          border: Border.all(color: MedixColors.border),
        ),
        child: child,
      ),
    );
  }
}

class UrgencyBadge extends StatelessWidget {
  final String level;
  const UrgencyBadge({super.key, required this.level});

  Color get _color => switch (level.toLowerCase()) {
    'critical' => MedixColors.critical,
    'high'     => MedixColors.danger,
    'medium'   => MedixColors.warning,
    _          => MedixColors.success,
  };

  String get _label => switch (level.toLowerCase()) {
    'critical' => '🔴 CRÍTICO',
    'high'     => '🟠 ALTO',
    'medium'   => '🟡 MEDIO',
    _          => '🟢 BAJO',
  };

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
      decoration: BoxDecoration(
        color: _color.withOpacity(0.15),
        borderRadius: BorderRadius.circular(20),
        border: Border.all(color: _color.withOpacity(0.5)),
      ),
      child: Text(
        _label,
        style: TextStyle(color: _color, fontSize: 12, fontWeight: FontWeight.w600),
      ),
    );
  }
}
