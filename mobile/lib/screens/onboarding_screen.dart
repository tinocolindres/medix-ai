import 'package:flutter/material.dart';
import 'package:shared_preferences/shared_preferences.dart';
import '../theme.dart';
import 'register_screen.dart';
import 'login_screen.dart';

class OnboardingScreen extends StatefulWidget {
  const OnboardingScreen({super.key});

  @override
  State<OnboardingScreen> createState() => _OnboardingScreenState();
}

class _OnboardingScreenState extends State<OnboardingScreen>
    with SingleTickerProviderStateMixin {
  final _pageCtrl = PageController();
  int _page = 0;

  final _pages = const [
    _OnboardPage(
      emoji: '🤖',
      title: 'Chat IA Médico Contextual',
      subtitle:
          'Respuestas adaptadas a tu rol:\nestudiante, médico general o especialista.\nContexto de tu universidad y año académico.',
      color: MedixColors.blue,
    ),
    _OnboardPage(
      emoji: '🔬',
      title: 'MedScan Vision',
      subtitle:
          'Analiza radiografías, resultados de laboratorio, recetas y ECGs.\nImpulsado por Claude AI Vision.',
      color: Color(0xFF8B5CF6),
    ),
    _OnboardPage(
      emoji: '🏥',
      title: 'Modo Guardia 100% Offline',
      subtitle:
          'Calculadoras clínicas sin internet:\nGlasgow, APGAR, Holiday-Segar,\nDosis pediátricas y más.',
      color: MedixColors.danger,
    ),
    _OnboardPage(
      emoji: '📋',
      title: 'Normas SESAL Honduras',
      subtitle:
          'Protocolos clínicos oficiales de la\nSecretaría de Salud de Honduras.\nSiempre actualizados.',
      color: Color(0xFF06B6D4),
    ),
    _OnboardPage(
      emoji: '📝',
      title: 'Dictado SOAP con IA',
      subtitle:
          'Dicta el caso clínico en lenguaje natural.\nMedix AI genera la nota de evolución\nestructurada lista para el expediente.',
      color: MedixColors.success,
      isLast: true,
    ),
  ];

  Future<void> _completeOnboarding() async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setBool('onboarding_done', true);
  }

  void _next() {
    if (_page < _pages.length - 1) {
      _pageCtrl.nextPage(
        duration: const Duration(milliseconds: 350),
        curve: Curves.easeInOut,
      );
    }
  }

  void _goToRegister() async {
    await _completeOnboarding();
    if (mounted) {
      Navigator.pushReplacement(context,
          MaterialPageRoute(builder: (_) => const RegisterScreen()));
    }
  }

  void _goToLogin() async {
    await _completeOnboarding();
    if (mounted) {
      Navigator.pushReplacement(context,
          MaterialPageRoute(builder: (_) => const LoginScreen()));
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: SafeArea(
        child: Column(
          children: [
            // Botón skip
            Align(
              alignment: Alignment.topRight,
              child: Padding(
                padding: const EdgeInsets.fromLTRB(0, 12, 16, 0),
                child: TextButton(
                  onPressed: _goToLogin,
                  child: const Text('Omitir',
                    style: TextStyle(color: MedixColors.textMuted)),
                ),
              ),
            ),

            // Páginas
            Expanded(
              child: PageView.builder(
                controller: _pageCtrl,
                itemCount: _pages.length,
                onPageChanged: (i) => setState(() => _page = i),
                itemBuilder: (_, i) => _pages[i],
              ),
            ),

            // Indicadores + botones
            Padding(
              padding: const EdgeInsets.fromLTRB(24, 0, 24, 32),
              child: Column(
                children: [
                  // Dots
                  Row(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: List.generate(_pages.length, (i) {
                      final isActive = i == _page;
                      final color = _pages[_page].color;
                      return AnimatedContainer(
                        duration: const Duration(milliseconds: 250),
                        margin: const EdgeInsets.symmetric(horizontal: 4),
                        width: isActive ? 24 : 8,
                        height: 8,
                        decoration: BoxDecoration(
                          color: isActive ? color : MedixColors.border,
                          borderRadius: BorderRadius.circular(4),
                        ),
                      );
                    }),
                  ),
                  const SizedBox(height: 28),

                  // Botón principal
                  ElevatedButton(
                    onPressed: _pages[_page].isLast ? _goToRegister : _next,
                    style: ElevatedButton.styleFrom(
                      backgroundColor: _pages[_page].color,
                    ),
                    child: Text(
                      _pages[_page].isLast ? 'Crear mi cuenta' : 'Siguiente',
                      style: const TextStyle(fontSize: 16),
                    ),
                  ),

                  const SizedBox(height: 14),

                  // Ya tengo cuenta
                  if (_pages[_page].isLast)
                    TextButton(
                      onPressed: _goToLogin,
                      child: const Text('Ya tengo cuenta — Ingresar',
                        style: TextStyle(color: MedixColors.textSecondary)),
                    ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _OnboardPage extends StatelessWidget {
  final String emoji, title, subtitle;
  final Color color;
  final bool isLast;

  const _OnboardPage({
    required this.emoji,
    required this.title,
    required this.subtitle,
    required this.color,
    this.isLast = false,
  });

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 32),
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          // Icono animado
          Container(
            width: 120,
            height: 120,
            decoration: BoxDecoration(
              color: color.withOpacity(0.12),
              shape: BoxShape.circle,
              border: Border.all(color: color.withOpacity(0.3), width: 2),
            ),
            child: Center(
              child: Text(emoji, style: const TextStyle(fontSize: 56)),
            ),
          ),
          const SizedBox(height: 40),

          Text(
            title,
            textAlign: TextAlign.center,
            style: const TextStyle(
              fontSize: 24, fontWeight: FontWeight.w800, height: 1.2),
          ),
          const SizedBox(height: 16),

          Text(
            subtitle,
            textAlign: TextAlign.center,
            style: const TextStyle(
              color: MedixColors.textSecondary,
              fontSize: 15,
              height: 1.7,
            ),
          ),
        ],
      ),
    );
  }
}
