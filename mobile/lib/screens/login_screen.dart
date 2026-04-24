import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../theme.dart';
import '../services/api.dart';
import 'home_screen.dart';
import 'register_screen.dart';

class LoginScreen extends ConsumerStatefulWidget {
  const LoginScreen({super.key});

  @override
  ConsumerState<LoginScreen> createState() => _LoginScreenState();
}

class _LoginScreenState extends ConsumerState<LoginScreen> {
  final _emailCtrl = TextEditingController();
  final _passCtrl = TextEditingController();
  bool _loading = false;
  bool _obscurePass = true;
  String? _error;

  Future<void> _login() async {
    setState(() { _loading = true; _error = null; });
    try {
      await ApiService().login(_emailCtrl.text.trim(), _passCtrl.text);
      if (mounted) {
        Navigator.pushReplacement(context, MaterialPageRoute(builder: (_) => const HomeScreen()));
      }
    } catch (e) {
      setState(() { _error = 'Correo o contraseña incorrectos'; });
    } finally {
      setState(() { _loading = false; });
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: SafeArea(
        child: SingleChildScrollView(
          padding: const EdgeInsets.all(24),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const SizedBox(height: 40),

              // ── Logo ──────────────────────────────────────────
              Center(
                child: Column(children: [
                  Container(
                    width: 72, height: 72,
                    decoration: BoxDecoration(
                      color: MedixColors.blue.withOpacity(0.15),
                      borderRadius: BorderRadius.circular(20),
                      border: Border.all(color: MedixColors.blue.withOpacity(0.4)),
                    ),
                    child: const Icon(Icons.medical_services_rounded,
                      size: 40, color: MedixColors.blue),
                  ),
                  const SizedBox(height: 16),
                  const Text('Medix AI',
                    style: TextStyle(fontSize: 28, fontWeight: FontWeight.w700)),
                  const SizedBox(height: 6),
                  const Text('Tu asistente médico inteligente',
                    style: TextStyle(color: MedixColors.textSecondary, fontSize: 14)),
                ]),
              ),

              const SizedBox(height: 48),

              // ── Formulario ────────────────────────────────────
              const Text('Iniciar sesión',
                style: TextStyle(fontSize: 22, fontWeight: FontWeight.w600)),
              const SizedBox(height: 24),

              TextFormField(
                controller: _emailCtrl,
                keyboardType: TextInputType.emailAddress,
                decoration: const InputDecoration(
                  labelText: 'Correo electrónico',
                  prefixIcon: Icon(Icons.email_outlined, color: MedixColors.textMuted),
                ),
              ),
              const SizedBox(height: 16),

              TextFormField(
                controller: _passCtrl,
                obscureText: _obscurePass,
                decoration: InputDecoration(
                  labelText: 'Contraseña',
                  prefixIcon: const Icon(Icons.lock_outline, color: MedixColors.textMuted),
                  suffixIcon: IconButton(
                    icon: Icon(_obscurePass ? Icons.visibility_off : Icons.visibility,
                      color: MedixColors.textMuted),
                    onPressed: () => setState(() => _obscurePass = !_obscurePass),
                  ),
                ),
                onFieldSubmitted: (_) => _login(),
              ),

              if (_error != null) ...[
                const SizedBox(height: 12),
                Container(
                  padding: const EdgeInsets.all(12),
                  decoration: BoxDecoration(
                    color: MedixColors.danger.withOpacity(0.1),
                    borderRadius: BorderRadius.circular(8),
                    border: Border.all(color: MedixColors.danger.withOpacity(0.3)),
                  ),
                  child: Row(children: [
                    const Icon(Icons.error_outline, color: MedixColors.danger, size: 18),
                    const SizedBox(width: 8),
                    Text(_error!, style: const TextStyle(color: MedixColors.danger, fontSize: 13)),
                  ]),
                ),
              ],

              const SizedBox(height: 28),

              ElevatedButton(
                onPressed: _loading ? null : _login,
                child: _loading
                    ? const SizedBox(height: 20, width: 20,
                        child: CircularProgressIndicator(color: Colors.white, strokeWidth: 2))
                    : const Text('Ingresar'),
              ),

              const SizedBox(height: 20),

              // ── Registro ──────────────────────────────────────
              Row(mainAxisAlignment: MainAxisAlignment.center, children: [
                const Text('¿No tienes cuenta? ',
                  style: TextStyle(color: MedixColors.textSecondary)),
                GestureDetector(
                  onTap: () => Navigator.push(context,
                    MaterialPageRoute(builder: (_) => const RegisterScreen())),
                  child: const Text('Crear cuenta',
                    style: TextStyle(color: MedixColors.blue, fontWeight: FontWeight.w600)),
                ),
              ]),

              const SizedBox(height: 32),

              // ── Separador ─────────────────────────────────────
              Row(children: [
                const Expanded(child: Divider(color: MedixColors.border)),
                const Padding(
                  padding: EdgeInsets.symmetric(horizontal: 12),
                  child: Text('Para médicos y estudiantes', style: TextStyle(color: MedixColors.textMuted, fontSize: 11)),
                ),
                const Expanded(child: Divider(color: MedixColors.border)),
              ]),

              const SizedBox(height: 16),

              // ── Roles disponibles ─────────────────────────────
              Row(mainAxisAlignment: MainAxisAlignment.spaceEvenly, children: [
                _RoleChip(icon: Icons.school_outlined, label: 'UNAH / UNICAH'),
                _RoleChip(icon: Icons.local_hospital_outlined, label: 'Médico General'),
                _RoleChip(icon: Icons.biotech_outlined, label: 'Especialista'),
              ]),
            ],
          ),
        ),
      ),
    );
  }
}

class _RoleChip extends StatelessWidget {
  final IconData icon;
  final String label;
  const _RoleChip({required this.icon, required this.label});

  @override
  Widget build(BuildContext context) {
    return Column(children: [
      Container(
        padding: const EdgeInsets.all(10),
        decoration: BoxDecoration(
          color: MedixColors.bgSurface,
          borderRadius: BorderRadius.circular(12),
          border: Border.all(color: MedixColors.border),
        ),
        child: Icon(icon, color: MedixColors.blue, size: 22),
      ),
      const SizedBox(height: 6),
      Text(label, style: const TextStyle(fontSize: 10, color: MedixColors.textSecondary)),
    ]);
  }
}
