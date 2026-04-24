import 'package:flutter/material.dart';
import '../theme.dart';
import 'chat_screen.dart';
import 'medscan_screen.dart';
import 'guardia_screen.dart';
import 'soap_screen.dart';
import 'profile_screen.dart';

class HomeScreen extends StatefulWidget {
  const HomeScreen({super.key});

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  int _currentIndex = 0;

  final _screens = const [
    _DashboardTab(),
    ChatScreen(),
    MedScanScreen(),
    GuardiaScreen(),
    ProfileScreen(),
  ];

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: IndexedStack(index: _currentIndex, children: _screens),
      bottomNavigationBar: Container(
        decoration: const BoxDecoration(
          border: Border(top: BorderSide(color: MedixColors.border)),
        ),
        child: BottomNavigationBar(
          currentIndex: _currentIndex,
          onTap: (i) => setState(() => _currentIndex = i),
          items: const [
            BottomNavigationBarItem(icon: Icon(Icons.home_outlined), activeIcon: Icon(Icons.home), label: 'Inicio'),
            BottomNavigationBarItem(icon: Icon(Icons.chat_bubble_outline), activeIcon: Icon(Icons.chat_bubble), label: 'Chat IA'),
            BottomNavigationBarItem(icon: Icon(Icons.document_scanner_outlined), activeIcon: Icon(Icons.document_scanner), label: 'MedScan'),
            BottomNavigationBarItem(icon: Icon(Icons.local_hospital_outlined), activeIcon: Icon(Icons.local_hospital), label: 'Guardia'),
            BottomNavigationBarItem(icon: Icon(Icons.person_outline), activeIcon: Icon(Icons.person), label: 'Perfil'),
          ],
        ),
      ),
    );
  }
}

// ── Dashboard principal ──────────────────────────────────────────
class _DashboardTab extends StatelessWidget {
  const _DashboardTab();

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Row(children: [
          Container(
            padding: const EdgeInsets.all(6),
            decoration: BoxDecoration(
              color: MedixColors.blue.withOpacity(0.15),
              borderRadius: BorderRadius.circular(8),
            ),
            child: const Icon(Icons.medical_services_rounded, color: MedixColors.blue, size: 20),
          ),
          const SizedBox(width: 10),
          const Text('Medix AI'),
        ]),
        actions: [
          IconButton(icon: const Icon(Icons.notifications_outlined), onPressed: () {}),
        ],
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(20),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // ── Bienvenida ────────────────────────────────────
            Container(
              width: double.infinity,
              padding: const EdgeInsets.all(20),
              decoration: BoxDecoration(
                gradient: LinearGradient(
                  colors: [MedixColors.blue.withOpacity(0.8), MedixColors.blueDark],
                  begin: Alignment.topLeft,
                  end: Alignment.bottomRight,
                ),
                borderRadius: BorderRadius.circular(20),
              ),
              child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                const Text('Buenos días, Doctor 👋',
                  style: TextStyle(color: Colors.white70, fontSize: 14)),
                const SizedBox(height: 4),
                const Text('¿En qué te ayudo hoy?',
                  style: TextStyle(color: Colors.white, fontSize: 20, fontWeight: FontWeight.w700)),
                const SizedBox(height: 16),
                Row(children: [
                  _QuickBtn(icon: Icons.chat_bubble_outline, label: 'Chat IA',
                    onTap: () {}),
                  const SizedBox(width: 8),
                  _QuickBtn(icon: Icons.document_scanner_outlined, label: 'Escanear',
                    onTap: () {}),
                  const SizedBox(width: 8),
                  _QuickBtn(icon: Icons.mic, label: 'SOAP',
                    onTap: () => Navigator.push(context,
                      MaterialPageRoute(builder: (_) => const SOAPScreen()))),
                ]),
              ]),
            ),

            const SizedBox(height: 24),

            // ── Módulos principales ───────────────────────────
            const Text('Módulos',
              style: TextStyle(fontSize: 16, fontWeight: FontWeight.w600)),
            const SizedBox(height: 14),

            GridView.count(
              shrinkWrap: true,
              physics: const NeverScrollableScrollPhysics(),
              crossAxisCount: 2,
              mainAxisSpacing: 12,
              crossAxisSpacing: 12,
              childAspectRatio: 1.3,
              children: const [
                _ModuleCard(
                  icon: Icons.psychology_outlined,
                  title: 'Chat IA Médico',
                  subtitle: 'Consultas contextualizadas',
                  color: MedixColors.blue,
                ),
                _ModuleCard(
                  icon: Icons.document_scanner_outlined,
                  title: 'MedScan',
                  subtitle: 'Análisis de imágenes',
                  color: Color(0xFF8B5CF6),
                ),
                _ModuleCard(
                  icon: Icons.mic_outlined,
                  title: 'Dictado SOAP',
                  subtitle: 'Notas de evolución',
                  color: MedixColors.success,
                ),
                _ModuleCard(
                  icon: Icons.local_hospital_outlined,
                  title: 'Modo Guardia',
                  subtitle: 'Calculadoras offline',
                  color: MedixColors.danger,
                ),
                _ModuleCard(
                  icon: Icons.school_outlined,
                  title: 'Simulador ECOE',
                  subtitle: 'Pacientes virtuales',
                  color: MedixColors.warning,
                ),
                _ModuleCard(
                  icon: Icons.policy_outlined,
                  title: 'Normas SESAL',
                  subtitle: 'Protocolos Honduras',
                  color: Color(0xFF06B6D4),
                ),
              ],
            ),

            const SizedBox(height: 24),

            // ── Disclaimer ───────────────────────────────────
            Container(
              padding: const EdgeInsets.all(14),
              decoration: BoxDecoration(
                color: MedixColors.bgSurface,
                borderRadius: BorderRadius.circular(12),
                border: Border.all(color: MedixColors.border),
              ),
              child: const Row(children: [
                Icon(Icons.info_outline, color: MedixColors.textMuted, size: 18),
                SizedBox(width: 10),
                Expanded(child: Text(
                  'Medix AI asiste la decisión clínica. El criterio final siempre es del médico responsable.',
                  style: TextStyle(fontSize: 11, color: MedixColors.textMuted),
                )),
              ]),
            ),
          ],
        ),
      ),
    );
  }
}

class _QuickBtn extends StatelessWidget {
  final IconData icon;
  final String label;
  final VoidCallback onTap;
  const _QuickBtn({required this.icon, required this.label, required this.onTap});

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onTap,
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
        decoration: BoxDecoration(
          color: Colors.white.withOpacity(0.2),
          borderRadius: BorderRadius.circular(8),
        ),
        child: Row(mainAxisSize: MainAxisSize.min, children: [
          Icon(icon, color: Colors.white, size: 16),
          const SizedBox(width: 6),
          Text(label, style: const TextStyle(color: Colors.white, fontSize: 13, fontWeight: FontWeight.w500)),
        ]),
      ),
    );
  }
}

class _ModuleCard extends StatelessWidget {
  final IconData icon;
  final String title;
  final String subtitle;
  final Color color;
  const _ModuleCard({required this.icon, required this.title, required this.subtitle, required this.color});

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: MedixColors.bgSurface,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: MedixColors.border),
      ),
      child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
        Container(
          padding: const EdgeInsets.all(8),
          decoration: BoxDecoration(
            color: color.withOpacity(0.15),
            borderRadius: BorderRadius.circular(10),
          ),
          child: Icon(icon, color: color, size: 22),
        ),
        const Spacer(),
        Text(title, style: const TextStyle(fontWeight: FontWeight.w600, fontSize: 13)),
        const SizedBox(height: 2),
        Text(subtitle, style: const TextStyle(color: MedixColors.textMuted, fontSize: 11)),
      ]),
    );
  }
}
