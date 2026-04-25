import 'package:flutter/material.dart';
import '../theme.dart';
import '../services/api.dart';
import 'home_screen.dart';

class RegisterScreen extends StatefulWidget {
  const RegisterScreen({super.key});

  @override
  State<RegisterScreen> createState() => _RegisterScreenState();
}

class _RegisterScreenState extends State<RegisterScreen> {
  final _formKey = GlobalKey<FormState>();
  final _firstNameCtrl = TextEditingController();
  final _lastNameCtrl = TextEditingController();
  final _emailCtrl = TextEditingController();
  final _passCtrl = TextEditingController();
  String _role = 'student';
  bool _loading = false;
  String? _error;

  final _roles = [
    {'value': 'student',              'label': 'Estudiante de Medicina',   'icon': Icons.school_outlined},
    {'value': 'medico_general',       'label': 'Médico General',            'icon': Icons.local_hospital_outlined},
    {'value': 'medico_especialista',  'label': 'Médico Especialista',       'icon': Icons.biotech_outlined},
  ];

  Future<void> _register() async {
    if (!_formKey.currentState!.validate()) return;
    setState(() { _loading = true; _error = null; });

    try {
      await ApiService().register({
        'first_name': _firstNameCtrl.text.trim(),
        'last_name': _lastNameCtrl.text.trim(),
        'email': _emailCtrl.text.trim(),
        'password': _passCtrl.text,
        'role': _role,
      });
      if (mounted) {
        Navigator.pushReplacement(context, MaterialPageRoute(builder: (_) => const HomeScreen()));
      }
    } catch (e) {
      setState(() { _error = e.toString(); });
    } finally {
      setState(() { _loading = false; });
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Crear cuenta')),
      body: SafeArea(
        child: SingleChildScrollView(
          padding: const EdgeInsets.all(24),
          child: Form(
            key: _formKey,
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const Text('¿Quién eres?',
                  style: TextStyle(fontSize: 18, fontWeight: FontWeight.w600)),
                const SizedBox(height: 16),

                // ── Selección de rol ──────────────────────────
                ...(_roles.map((r) => Padding(
                  padding: const EdgeInsets.only(bottom: 8),
                  child: GestureDetector(
                    onTap: () => setState(() => _role = r['value'] as String),
                    child: Container(
                      padding: const EdgeInsets.all(14),
                      decoration: BoxDecoration(
                        color: _role == r['value']
                          ? MedixColors.blue.withOpacity(0.1)
                          : MedixColors.bgSurface,
                        borderRadius: BorderRadius.circular(12),
                        border: Border.all(
                          color: _role == r['value'] ? MedixColors.blue : MedixColors.border,
                          width: _role == r['value'] ? 2 : 1,
                        ),
                      ),
                      child: Row(children: [
                        Icon(r['icon'] as IconData,
                          color: _role == r['value'] ? MedixColors.blue : MedixColors.textMuted),
                        const SizedBox(width: 12),
                        Text(r['label'] as String,
                          style: TextStyle(
                            color: _role == r['value'] ? MedixColors.textPrimary : MedixColors.textSecondary,
                            fontWeight: _role == r['value'] ? FontWeight.w600 : FontWeight.normal,
                          )),
                        const Spacer(),
                        if (_role == r['value'])
                          const Icon(Icons.check_circle, color: MedixColors.blue, size: 20),
                      ]),
                    ),
                  ),
                ))),

                const SizedBox(height: 24),
                const Text('Datos personales',
                  style: TextStyle(fontSize: 18, fontWeight: FontWeight.w600)),
                const SizedBox(height: 16),

                Row(children: [
                  Expanded(child: TextFormField(
                    controller: _firstNameCtrl,
                    decoration: const InputDecoration(labelText: 'Nombre'),
                    validator: (v) => v!.isEmpty ? 'Requerido' : null,
                  )),
                  const SizedBox(width: 12),
                  Expanded(child: TextFormField(
                    controller: _lastNameCtrl,
                    decoration: const InputDecoration(labelText: 'Apellido'),
                    validator: (v) => v!.isEmpty ? 'Requerido' : null,
                  )),
                ]),
                const SizedBox(height: 16),

                TextFormField(
                  controller: _emailCtrl,
                  keyboardType: TextInputType.emailAddress,
                  decoration: const InputDecoration(
                    labelText: 'Correo electrónico',
                    prefixIcon: Icon(Icons.email_outlined, color: MedixColors.textMuted),
                  ),
                  validator: (v) => !v!.contains('@') ? 'Correo inválido' : null,
                ),
                const SizedBox(height: 16),

                TextFormField(
                  controller: _passCtrl,
                  obscureText: true,
                  decoration: const InputDecoration(
                    labelText: 'Contraseña',
                    prefixIcon: Icon(Icons.lock_outline, color: MedixColors.textMuted),
                    hintText: 'Mínimo 8 caracteres',
                  ),
                  validator: (v) => v!.length < 8 ? 'Mínimo 8 caracteres' : null,
                ),

                if (_error != null) ...[
                  const SizedBox(height: 12),
                  Text(_error!, style: const TextStyle(color: MedixColors.danger)),
                ],

                const SizedBox(height: 28),

                ElevatedButton(
                  onPressed: _loading ? null : _register,
                  child: _loading
                    ? const SizedBox(height: 20, width: 20,
                        child: CircularProgressIndicator(color: Colors.white, strokeWidth: 2))
                    : const Text('Crear mi cuenta'),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}
