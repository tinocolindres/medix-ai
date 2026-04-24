import 'package:flutter/material.dart';
import 'package:flutter_markdown/flutter_markdown.dart';
import '../theme.dart';
import '../services/api.dart';

class SESALScreen extends StatefulWidget {
  const SESALScreen({super.key});

  @override
  State<SESALScreen> createState() => _SESALScreenState();
}

class _SESALScreenState extends State<SESALScreen> {
  final _queryCtrl = TextEditingController();
  bool _loading = false;
  Map<String, dynamic>? _result;

  // Consultas frecuentes de guardia
  final _quickQueries = [
    '¿Cuál es el manejo del dengue hemorrágico según SESAL?',
    '¿Dosis de amoxicilina pediátrica en neumonía?',
    '¿Protocolo de crisis hipertensiva en Honduras?',
    '¿Manejo de malaria en zona rural sin laboratorio?',
    '¿Control prenatal normas SESAL cuántas consultas?',
    '¿Tratamiento TB primera línea Honduras?',
  ];

  Future<void> _query(String q) async {
    _queryCtrl.text = q;
    setState(() { _loading = true; _result = null; });

    try {
      final result = await ApiService().querySESAL(q);
      setState(() => _result = result);
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Error: $e'), backgroundColor: MedixColors.danger),
        );
      }
    } finally {
      setState(() => _loading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Row(children: [
          Container(
            padding: const EdgeInsets.all(6),
            decoration: BoxDecoration(
              color: const Color(0xFF06B6D4).withOpacity(0.15),
              borderRadius: BorderRadius.circular(8),
            ),
            child: const Icon(Icons.policy_outlined, color: Color(0xFF06B6D4), size: 20),
          ),
          const SizedBox(width: 10),
          const Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
            Text('Normas SESAL', style: TextStyle(fontSize: 15)),
            Text('Honduras oficial', style: TextStyle(color: Color(0xFF06B6D4), fontSize: 11)),
          ]),
        ]),
      ),
      body: Column(
        children: [
          // ── Header informativo ────────────────────────────
          Container(
            margin: const EdgeInsets.fromLTRB(16, 12, 16, 0),
            padding: const EdgeInsets.all(14),
            decoration: BoxDecoration(
              color: const Color(0xFF06B6D4).withOpacity(0.1),
              borderRadius: BorderRadius.circular(12),
              border: Border.all(color: const Color(0xFF06B6D4).withOpacity(0.3)),
            ),
            child: const Row(children: [
              Icon(Icons.verified_outlined, color: Color(0xFF06B6D4), size: 18),
              SizedBox(width: 10),
              Expanded(child: Text(
                'Respuestas basadas en guías clínicas oficiales de la Secretaría de Salud de Honduras (SESAL).',
                style: TextStyle(color: Color(0xFF06B6D4), fontSize: 12),
              )),
            ]),
          ),

          // ── Buscador ──────────────────────────────────────
          Padding(
            padding: const EdgeInsets.fromLTRB(16, 14, 16, 0),
            child: Row(children: [
              Expanded(
                child: TextField(
                  controller: _queryCtrl,
                  decoration: const InputDecoration(
                    hintText: 'Consulta un protocolo o norma...',
                    prefixIcon: Icon(Icons.search, color: MedixColors.textMuted),
                  ),
                  onSubmitted: (v) { if (v.trim().isNotEmpty) _query(v.trim()); },
                ),
              ),
              const SizedBox(width: 10),
              GestureDetector(
                onTap: () {
                  final q = _queryCtrl.text.trim();
                  if (q.isNotEmpty) _query(q);
                },
                child: Container(
                  width: 46, height: 46,
                  decoration: BoxDecoration(
                    color: _loading ? MedixColors.border : const Color(0xFF06B6D4),
                    borderRadius: BorderRadius.circular(12),
                  ),
                  child: _loading
                    ? const Padding(
                        padding: EdgeInsets.all(12),
                        child: CircularProgressIndicator(color: Colors.white, strokeWidth: 2))
                    : const Icon(Icons.send_rounded, color: Colors.white, size: 20),
                ),
              ),
            ]),
          ),

          const SizedBox(height: 12),

          // ── Consultas rápidas ─────────────────────────────
          if (_result == null && !_loading)
            SizedBox(
              height: 38,
              child: ListView.separated(
                scrollDirection: Axis.horizontal,
                padding: const EdgeInsets.symmetric(horizontal: 16),
                itemCount: _quickQueries.length,
                separatorBuilder: (_, __) => const SizedBox(width: 8),
                itemBuilder: (ctx, i) => GestureDetector(
                  onTap: () => _query(_quickQueries[i]),
                  child: Container(
                    padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
                    decoration: BoxDecoration(
                      color: MedixColors.bgSurface,
                      borderRadius: BorderRadius.circular(20),
                      border: Border.all(color: MedixColors.border),
                    ),
                    child: Text(
                      _quickQueries[i].length > 35
                        ? '${_quickQueries[i].substring(0, 35)}...'
                        : _quickQueries[i],
                      style: const TextStyle(color: MedixColors.textSecondary, fontSize: 12),
                    ),
                  ),
                ),
              ),
            ),

          // ── Resultado ─────────────────────────────────────
          Expanded(
            child: _loading
              ? const Center(
                  child: Column(mainAxisAlignment: MainAxisAlignment.center, children: [
                    CircularProgressIndicator(color: Color(0xFF06B6D4)),
                    SizedBox(height: 16),
                    Text('Consultando normas SESAL...',
                      style: TextStyle(color: MedixColors.textSecondary)),
                  ]),
                )
              : _result == null
                ? _EmptySESAL()
                : SingleChildScrollView(
                    padding: const EdgeInsets.all(16),
                    child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                      // Fuente
                      Container(
                        padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
                        decoration: BoxDecoration(
                          color: MedixColors.bgSurface,
                          borderRadius: BorderRadius.circular(8),
                          border: Border.all(color: MedixColors.border),
                        ),
                        child: Row(children: [
                          const Icon(Icons.source_outlined,
                            color: MedixColors.textMuted, size: 14),
                          const SizedBox(width: 6),
                          Expanded(
                            child: Text(
                              _result!['source'] ?? 'SESAL Honduras',
                              style: const TextStyle(
                                color: MedixColors.textMuted, fontSize: 11),
                            ),
                          ),
                          if ((_result!['chunks_used'] ?? 0) > 0)
                            Text(
                              '${_result!['chunks_used']} fragmentos',
                              style: const TextStyle(
                                color: MedixColors.textMuted, fontSize: 10),
                            ),
                        ]),
                      ),
                      const SizedBox(height: 14),

                      // Respuesta
                      Container(
                        padding: const EdgeInsets.all(16),
                        decoration: BoxDecoration(
                          color: MedixColors.bgSurface,
                          borderRadius: BorderRadius.circular(14),
                          border: Border.all(
                            color: const Color(0xFF06B6D4).withOpacity(0.3)),
                        ),
                        child: MarkdownBody(
                          data: _result!['response'] ?? '',
                          styleSheet: MarkdownStyleSheet(
                            h2: const TextStyle(
                              color: Color(0xFF06B6D4),
                              fontSize: 16, fontWeight: FontWeight.w700),
                            h3: const TextStyle(
                              color: MedixColors.textPrimary,
                              fontSize: 14, fontWeight: FontWeight.w600),
                            p: const TextStyle(
                              color: MedixColors.textPrimary, height: 1.6, fontSize: 13),
                            strong: const TextStyle(
                              color: MedixColors.textPrimary,
                              fontWeight: FontWeight.w600),
                            listBullet: const TextStyle(color: Color(0xFF06B6D4)),
                          ),
                        ),
                      ),
                      const SizedBox(height: 12),

                      // Disclaimer
                      const Text(
                        '⚕️ Información basada en guías SESAL. '
                        'Siempre valida con la versión vigente del documento oficial.',
                        style: TextStyle(color: MedixColors.textMuted, fontSize: 11),
                      ),

                      // Nueva consulta
                      const SizedBox(height: 16),
                      TextButton.icon(
                        onPressed: () => setState(() {
                          _result = null;
                          _queryCtrl.clear();
                        }),
                        icon: const Icon(Icons.refresh, size: 16),
                        label: const Text('Nueva consulta'),
                      ),
                    ]),
                  ),
          ),
        ],
      ),
    );
  }
}

class _EmptySESAL extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(32),
        child: Column(mainAxisAlignment: MainAxisAlignment.center, children: [
          Container(
            padding: const EdgeInsets.all(24),
            decoration: BoxDecoration(
              color: const Color(0xFF06B6D4).withOpacity(0.1),
              shape: BoxShape.circle,
            ),
            child: const Icon(Icons.policy_outlined,
              color: Color(0xFF06B6D4), size: 48),
          ),
          const SizedBox(height: 20),
          const Text('Normas SESAL Honduras',
            style: TextStyle(fontSize: 18, fontWeight: FontWeight.w600)),
          const SizedBox(height: 8),
          const Text(
            'Consulta protocolos clínicos oficiales: '
            'dengue, malaria, tuberculosis, diabetes, '
            'hipertensión, atención prenatal y más.',
            textAlign: TextAlign.center,
            style: TextStyle(color: MedixColors.textSecondary, height: 1.5),
          ),
          const SizedBox(height: 20),
          const Text('Usa las sugerencias de arriba para comenzar',
            style: TextStyle(color: MedixColors.textMuted, fontSize: 12)),
        ]),
      ),
    );
  }
}
