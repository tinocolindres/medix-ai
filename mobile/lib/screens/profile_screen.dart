import 'package:flutter/material.dart';
import '../theme.dart';
import '../services/api.dart';
import 'login_screen.dart';

class ProfileScreen extends StatefulWidget {
  const ProfileScreen({super.key});
  @override
  State<ProfileScreen> createState() => _ProfileScreenState();
}

class _ProfileScreenState extends State<ProfileScreen> {
  Map<String, dynamic>? _user;
  bool _loading = true;

  @override
  void initState() {
    super.initState();
    _loadProfile();
  }

  Future<void> _loadProfile() async {
    try {
      final user = await ApiService().getMe();
      setState(() { _user = user; _loading = false; });
    } catch (_) {
      setState(() => _loading = false);
    }
  }

  Future<void> _logout() async {
    await ApiService().logout();
    if (mounted) {
      Navigator.pushReplacement(context, MaterialPageRoute(builder: (_) => const LoginScreen()));
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Perfil')),
      body: _loading
        ? const Center(child: CircularProgressIndicator(color: MedixColors.blue))
        : SingleChildScrollView(
            padding: const EdgeInsets.all(20),
            child: Column(
              children: [
                // ── Avatar ──────────────────────────────────
                Container(
                  width: 80, height: 80,
                  decoration: BoxDecoration(
                    color: MedixColors.blue.withOpacity(0.15),
                    shape: BoxShape.circle,
                    border: Border.all(color: MedixColors.blue.withOpacity(0.3), width: 2),
                  ),
                  child: const Icon(Icons.person, color: MedixColors.blue, size: 40),
                ),
                const SizedBox(height: 12),

                if (_user != null) ...[
                  Text('${_user!['first_name']} ${_user!['last_name']}',
                    style: const TextStyle(fontSize: 20, fontWeight: FontWeight.w700)),
                  const SizedBox(height: 4),
                  Text(_user!['email'] ?? '',
                    style: const TextStyle(color: MedixColors.textSecondary)),
                  const SizedBox(height: 8),
                  _PlanBadge(tier: _user!['subscription_tier'] ?? 'free'),
                ],

                const SizedBox(height: 28),

                // ── Plan info ────────────────────────────────
                const _SectionTitle('Mi Plan'),
                const SizedBox(height: 10),
                _PlanCard(),

                const SizedBox(height: 20),

                // ── Configuración ────────────────────────────
                const _SectionTitle('Configuración'),
                const SizedBox(height: 10),

                _SettingTile(icon: Icons.school_outlined, label: 'Universidad y período'),
                _SettingTile(icon: Icons.notifications_outlined, label: 'Notificaciones'),
                _SettingTile(icon: Icons.lock_outline, label: 'Cambiar contraseña'),
                _SettingTile(icon: Icons.help_outline, label: 'Soporte'),

                const SizedBox(height: 20),

                // ── Logout ───────────────────────────────────
                OutlinedButton.icon(
                  onPressed: _logout,
                  icon: const Icon(Icons.logout, color: MedixColors.danger),
                  label: const Text('Cerrar sesión',
                    style: TextStyle(color: MedixColors.danger)),
                  style: OutlinedButton.styleFrom(
                    minimumSize: const Size(double.infinity, 48),
                    side: const BorderSide(color: MedixColors.danger),
                    shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                  ),
                ),
              ],
            ),
          ),
    );
  }
}

class _PlanBadge extends StatelessWidget {
  final String tier;
  const _PlanBadge({required this.tier});

  @override
  Widget build(BuildContext context) {
    final config = switch (tier) {
      'pro'      => {'label': 'PRO', 'color': MedixColors.blue},
      'clinical' => {'label': 'CLINICAL', 'color': const Color(0xFF8B5CF6)},
      _          => {'label': 'FREE', 'color': MedixColors.textMuted},
    };
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 4),
      decoration: BoxDecoration(
        color: (config['color'] as Color).withOpacity(0.15),
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: (config['color'] as Color).withOpacity(0.4)),
      ),
      child: Text(config['label'] as String,
        style: TextStyle(color: config['color'] as Color, fontWeight: FontWeight.w600, fontSize: 12)),
    );
  }
}

class _PlanCard extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        gradient: LinearGradient(
          colors: [MedixColors.blue.withOpacity(0.2), MedixColors.bgSurface],
          begin: Alignment.topLeft, end: Alignment.bottomRight,
        ),
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: MedixColors.border),
      ),
      child: Column(children: [
        const Row(mainAxisAlignment: MainAxisAlignment.spaceBetween, children: [
          Text('Plan Free', style: TextStyle(fontWeight: FontWeight.w700, fontSize: 16)),
          Text('L 0 / mes', style: TextStyle(color: MedixColors.textSecondary)),
        ]),
        const SizedBox(height: 12),
        const _PlanFeature(text: '20 mensajes de chat / día', available: true),
        const _PlanFeature(text: '3 MedScans / día', available: true),
        const _PlanFeature(text: 'Modo Guardia (offline)', available: true),
        const _PlanFeature(text: 'Dictado SOAP', available: false),
        const _PlanFeature(text: 'Chat ilimitado (Pro)', available: false),
        const SizedBox(height: 14),
        ElevatedButton(
          onPressed: () {},
          child: const Text('Mejorar a Pro — L 299/mes'),
        ),
      ]),
    );
  }
}

class _PlanFeature extends StatelessWidget {
  final String text;
  final bool available;
  const _PlanFeature({required this.text, required this.available});

  @override
  Widget build(BuildContext context) => Padding(
    padding: const EdgeInsets.symmetric(vertical: 3),
    child: Row(children: [
      Icon(available ? Icons.check_circle_outline : Icons.cancel_outlined,
        color: available ? MedixColors.success : MedixColors.textMuted, size: 16),
      const SizedBox(width: 8),
      Text(text, style: TextStyle(
        color: available ? MedixColors.textPrimary : MedixColors.textMuted, fontSize: 13)),
    ]),
  );
}

class _SectionTitle extends StatelessWidget {
  final String text;
  const _SectionTitle(this.text);
  @override
  Widget build(BuildContext context) => Align(
    alignment: Alignment.centerLeft,
    child: Text(text, style: const TextStyle(fontSize: 14, fontWeight: FontWeight.w600,
      color: MedixColors.textSecondary)),
  );
}

class _SettingTile extends StatelessWidget {
  final IconData icon;
  final String label;
  const _SettingTile({required this.icon, required this.label});

  @override
  Widget build(BuildContext context) => Container(
    margin: const EdgeInsets.only(bottom: 8),
    child: ListTile(
      leading: Icon(icon, color: MedixColors.textSecondary),
      title: Text(label),
      trailing: const Icon(Icons.chevron_right, color: MedixColors.textMuted),
      tileColor: MedixColors.bgSurface,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
      onTap: () {},
    ),
  );
}
