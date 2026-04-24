import 'package:flutter/material.dart';
import 'package:url_launcher/url_launcher.dart';
import '../theme.dart';
import '../services/api.dart';

class UpgradeScreen extends StatefulWidget {
  const UpgradeScreen({super.key});

  @override
  State<UpgradeScreen> createState() => _UpgradeScreenState();
}

class _UpgradeScreenState extends State<UpgradeScreen> {
  bool _loadingPro = false;
  bool _loadingClinical = false;

  Future<void> _checkout(String plan) async {
    setState(() {
      if (plan == 'pro') _loadingPro = true;
      else _loadingClinical = true;
    });

    try {
      final result = await ApiService().createCheckout(plan);
      final url = result['checkout_url'] as String;
      final uri = Uri.parse(url);
      if (await canLaunchUrl(uri)) {
        await launchUrl(uri, mode: LaunchMode.externalApplication);
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('Error al procesar pago: $e'),
            backgroundColor: MedixColors.danger,
          ),
        );
      }
    } finally {
      setState(() { _loadingPro = false; _loadingClinical = false; });
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Mejora tu plan')),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(20),
        child: Column(
          children: [
            // ── Header ────────────────────────────────────────
            Container(
              width: double.infinity,
              padding: const EdgeInsets.all(20),
              decoration: BoxDecoration(
                gradient: LinearGradient(
                  colors: [const Color(0xFF1e3a5f), MedixColors.bgSurface],
                  begin: Alignment.topLeft,
                  end: Alignment.bottomRight,
                ),
                borderRadius: BorderRadius.circular(20),
                border: Border.all(color: MedixColors.border),
              ),
              child: const Column(children: [
                Icon(Icons.workspace_premium_rounded, color: Color(0xFFFFD700), size: 48),
                SizedBox(height: 12),
                Text('Desbloquea todo Medix AI',
                  style: TextStyle(fontSize: 20, fontWeight: FontWeight.w700)),
                SizedBox(height: 6),
                Text('Herramientas que salvan tiempo en cada turno',
                  textAlign: TextAlign.center,
                  style: TextStyle(color: MedixColors.textSecondary)),
              ]),
            ),

            const SizedBox(height: 24),

            // ── Plan Pro ──────────────────────────────────────
            _PlanCard(
              name: 'Pro',
              price: 'L 299',
              period: 'por mes',
              color: MedixColors.blue,
              features: const [
                '✅ 500 mensajes de chat / día',
                '✅ 50 MedScans por día',
                '✅ Dictado SOAP ilimitado',
                '✅ Simulador ECOE completo',
                '✅ Normas SESAL Honduras',
                '✅ Modo Guardia offline',
                '✅ Soporte prioritario',
              ],
              loading: _loadingPro,
              onTap: () => _checkout('pro'),
            ),

            const SizedBox(height: 16),

            // ── Plan Clinical ─────────────────────────────────
            _PlanCard(
              name: 'Clinical',
              price: 'L 799',
              period: 'por mes',
              color: const Color(0xFF8B5CF6),
              badge: '⭐ Especialistas',
              features: const [
                '✅ Todo lo de Pro',
                '✅ MedScan ILIMITADO',
                '✅ Respuestas prioritarias (menor latencia)',
                '✅ Análisis avanzado de imágenes',
                '✅ Red de interconsulta segura (próx.)',
                '✅ Acceso beta a nuevas funciones',
              ],
              loading: _loadingClinical,
              onTap: () => _checkout('clinical'),
            ),

            const SizedBox(height: 24),

            // ── Comparativa ───────────────────────────────────
            const Text('Comparativa completa',
              style: TextStyle(fontWeight: FontWeight.w600, fontSize: 16)),
            const SizedBox(height: 12),

            _ComparisonTable(),

            const SizedBox(height: 20),

            // ── Seguridad pago ────────────────────────────────
            Container(
              padding: const EdgeInsets.all(14),
              decoration: BoxDecoration(
                color: MedixColors.bgSurface,
                borderRadius: BorderRadius.circular(12),
                border: Border.all(color: MedixColors.border),
              ),
              child: const Row(children: [
                Icon(Icons.lock_outline, color: MedixColors.success, size: 20),
                SizedBox(width: 10),
                Expanded(child: Text(
                  'Pago seguro procesado por Stripe. Cancela en cualquier momento. Sin contratos.',
                  style: TextStyle(color: MedixColors.textSecondary, fontSize: 12),
                )),
              ]),
            ),
          ],
        ),
      ),
    );
  }
}

class _PlanCard extends StatelessWidget {
  final String name, price, period;
  final Color color;
  final List<String> features;
  final bool loading;
  final VoidCallback onTap;
  final String? badge;

  const _PlanCard({
    required this.name,
    required this.price,
    required this.period,
    required this.color,
    required this.features,
    required this.loading,
    required this.onTap,
    this.badge,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        color: MedixColors.bgSurface,
        borderRadius: BorderRadius.circular(20),
        border: Border.all(color: color.withOpacity(0.5), width: 2),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(children: [
            Text(name,
              style: TextStyle(fontSize: 20, fontWeight: FontWeight.w700, color: color)),
            if (badge != null) ...[
              const SizedBox(width: 8),
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                decoration: BoxDecoration(
                  color: color.withOpacity(0.15),
                  borderRadius: BorderRadius.circular(10),
                ),
                child: Text(badge!, style: TextStyle(color: color, fontSize: 11)),
              ),
            ],
          ]),
          const SizedBox(height: 8),
          Row(crossAxisAlignment: CrossAxisAlignment.end, children: [
            Text(price, style: const TextStyle(fontSize: 32, fontWeight: FontWeight.w800)),
            const SizedBox(width: 4),
            Padding(
              padding: const EdgeInsets.only(bottom: 4),
              child: Text(period, style: const TextStyle(color: MedixColors.textSecondary)),
            ),
          ]),
          const SizedBox(height: 16),
          ...features.map((f) => Padding(
            padding: const EdgeInsets.only(bottom: 6),
            child: Text(f, style: const TextStyle(fontSize: 13)),
          )),
          const SizedBox(height: 16),
          ElevatedButton(
            onPressed: loading ? null : onTap,
            style: ElevatedButton.styleFrom(backgroundColor: color),
            child: loading
              ? const SizedBox(width: 20, height: 20,
                  child: CircularProgressIndicator(color: Colors.white, strokeWidth: 2))
              : Text('Contratar $name'),
          ),
        ],
      ),
    );
  }
}

class _ComparisonTable extends StatelessWidget {
  final _rows = const [
    ['Chat IA/día',   '20',      '500',     '500'],
    ['MedScan/día',   '3',       '50',      '∞'],
    ['Dictado SOAP',  '❌',      '✅',      '✅'],
    ['SESAL RAG',     '✅',      '✅',      '✅'],
    ['Modo Guardia',  '✅',      '✅',      '✅'],
    ['Prioridad',     '❌',      '❌',      '✅'],
    ['Precio/mes',    'L 0',     'L 299',   'L 799'],
  ];

  const _ComparisonTable();

  @override
  Widget build(BuildContext context) {
    return Container(
      decoration: BoxDecoration(
        color: MedixColors.bgSurface,
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: MedixColors.border),
      ),
      child: Table(
        border: TableBorder.symmetric(
          inside: const BorderSide(color: MedixColors.border, width: 0.5),
        ),
        columnWidths: const {0: FlexColumnWidth(2), 1: FlexColumnWidth(1), 2: FlexColumnWidth(1), 3: FlexColumnWidth(1)},
        children: [
          TableRow(
            decoration: const BoxDecoration(
              color: MedixColors.bgElevated,
              borderRadius: BorderRadius.vertical(top: Radius.circular(12)),
            ),
            children: ['Función', 'Free', 'Pro', 'Clinical'].map((h) => Padding(
              padding: const EdgeInsets.all(10),
              child: Text(h, style: const TextStyle(fontWeight: FontWeight.w700, fontSize: 12),
                textAlign: h == 'Función' ? TextAlign.left : TextAlign.center),
            )).toList(),
          ),
          ..._rows.map((row) => TableRow(
            children: row.asMap().entries.map((e) => Padding(
              padding: const EdgeInsets.symmetric(vertical: 8, horizontal: 10),
              child: Text(e.value,
                style: TextStyle(
                  fontSize: 12,
                  color: e.value == '❌' ? MedixColors.textMuted : MedixColors.textPrimary,
                ),
                textAlign: e.key == 0 ? TextAlign.left : TextAlign.center),
            )).toList(),
          )),
        ],
      ),
    );
  }
}
