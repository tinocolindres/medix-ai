import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:shared_preferences/shared_preferences.dart';

import 'theme.dart';
import 'screens/login_screen.dart';
import 'screens/home_screen.dart';
import 'screens/onboarding_screen.dart';
import 'services/api.dart';
import 'services/notifications.dart';
import 'services/connectivity.dart';

void main() async {
  WidgetsFlutterBinding.ensureInitialized();
  SystemChrome.setSystemUIOverlayStyle(const SystemUiOverlayStyle(
    statusBarColor: Colors.transparent,
    statusBarIconBrightness: Brightness.light,
  ));
  await Future.wait([
    NotificationService().init(),
    ConnectivityService().init(),
  ]);
  runApp(const ProviderScope(child: MedixApp()));
}

final appStateProvider = FutureProvider<_AppState>((ref) async {
  final prefs = await SharedPreferences.getInstance();
  final onboardingDone = prefs.getBool('onboarding_done') ?? false;
  final isLoggedIn = await ApiService().isLoggedIn();
  return _AppState(onboardingDone: onboardingDone, isLoggedIn: isLoggedIn);
});

class _AppState {
  final bool onboardingDone;
  final bool isLoggedIn;
  const _AppState({required this.onboardingDone, required this.isLoggedIn});
}

class MedixApp extends ConsumerWidget {
  const MedixApp({super.key});
  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final state = ref.watch(appStateProvider);
    return MaterialApp(
      title: 'Medix AI',
      theme: MedixTheme.dark,
      debugShowCheckedModeBanner: false,
      home: state.when(
        data: (s) {
          if (!s.onboardingDone) return const OnboardingScreen();
          if (s.isLoggedIn) return const HomeScreen();
          return const LoginScreen();
        },
        loading: () => const _SplashScreen(),
        error: (_, __) => const LoginScreen(),
      ),
    );
  }
}

class _SplashScreen extends StatelessWidget {
  const _SplashScreen();
  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: MedixColors.bgPrimary,
      body: Center(
        child: Column(mainAxisAlignment: MainAxisAlignment.center, children: [
          Container(
            width: 90, height: 90,
            decoration: BoxDecoration(
              color: MedixColors.blue.withOpacity(0.15),
              borderRadius: BorderRadius.circular(28),
              border: Border.all(color: MedixColors.blue.withOpacity(0.3)),
            ),
            child: const Icon(Icons.medical_services_rounded, size: 50, color: MedixColors.blue),
          ),
          const SizedBox(height: 24),
          const Text('Medix AI',
            style: TextStyle(fontSize: 30, fontWeight: FontWeight.w800, color: MedixColors.textPrimary)),
          const SizedBox(height: 6),
          const Text('Plataforma médica • Honduras',
            style: TextStyle(color: MedixColors.textSecondary, fontSize: 14)),
          const SizedBox(height: 40),
          const SizedBox(width: 28, height: 28,
            child: CircularProgressIndicator(color: MedixColors.blue, strokeWidth: 2.5)),
        ]),
      ),
    );
  }
}
