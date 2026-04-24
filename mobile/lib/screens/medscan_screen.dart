import 'package:flutter/material.dart';
import 'package:image_picker/image_picker.dart';
import 'package:flutter_markdown/flutter_markdown.dart';
import '../theme.dart';
import '../services/api.dart';

class MedScanScreen extends StatefulWidget {
  const MedScanScreen({super.key});

  @override
  State<MedScanScreen> createState() => _MedScanScreenState();
}

class _MedScanScreenState extends State<MedScanScreen> {
  final _picker = ImagePicker();
  bool _analyzing = false;
  Map<String, dynamic>? _result;
  String _scanType = 'other';
  XFile? _selectedImage;

  final _scanTypes = [
    {'value': 'prescription', 'label': 'Receta Médica',     'icon': Icons.receipt_outlined},
    {'value': 'xray',         'label': 'Radiografía',        'icon': Icons.image_outlined},
    {'value': 'lab_result',   'label': 'Laboratorio',        'icon': Icons.science_outlined},
    {'value': 'ecg',          'label': 'ECG',                'icon': Icons.monitor_heart_outlined},
    {'value': 'ultrasound',   'label': 'Ultrasonido',        'icon': Icons.radar_outlined},
    {'value': 'other',        'label': 'Otro',               'icon': Icons.image_search_outlined},
  ];

  Future<void> _pickImage(ImageSource source) async {
    final file = await _picker.pickImage(source: source, imageQuality: 85);
    if (file == null) return;
    setState(() { _selectedImage = file; _result = null; });
  }

  Future<void> _analyze() async {
    if (_selectedImage == null) return;
    setState(() => _analyzing = true);

    try {
      final bytes = await _selectedImage!.readAsBytes();
      final mime = _selectedImage!.mimeType ?? 'image/jpeg';

      final response = await ApiService().uploadScan(
        imageBytes: bytes,
        fileName: _selectedImage!.name,
        mimeType: mime,
        scanType: _scanType,
      );
      setState(() => _result = response);
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Error: $e'), backgroundColor: MedixColors.danger),
        );
      }
    } finally {
      setState(() => _analyzing = false);
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
              color: const Color(0xFF8B5CF6).withOpacity(0.15),
              borderRadius: BorderRadius.circular(8),
            ),
            child: const Icon(Icons.document_scanner_rounded, color: Color(0xFF8B5CF6), size: 20),
          ),
          const SizedBox(width: 10),
          const Text('MedScan Vision'),
        ]),
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(20),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // ── Tipo de imagen ─────────────────────────────
            const Text('Tipo de imagen', style: TextStyle(fontWeight: FontWeight.w600)),
            const SizedBox(height: 10),
            SizedBox(
              height: 80,
              child: ListView.separated(
                scrollDirection: Axis.horizontal,
                itemCount: _scanTypes.length,
                separatorBuilder: (_, __) => const SizedBox(width: 8),
                itemBuilder: (ctx, i) {
                  final t = _scanTypes[i];
                  final selected = _scanType == t['value'];
                  return GestureDetector(
                    onTap: () => setState(() => _scanType = t['value'] as String),
                    child: Container(
                      padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
                      decoration: BoxDecoration(
                        color: selected ? const Color(0xFF8B5CF6).withOpacity(0.15) : MedixColors.bgSurface,
                        borderRadius: BorderRadius.circular(12),
                        border: Border.all(
                          color: selected ? const Color(0xFF8B5CF6) : MedixColors.border,
                          width: selected ? 2 : 1,
                        ),
                      ),
                      child: Column(mainAxisAlignment: MainAxisAlignment.center, children: [
                        Icon(t['icon'] as IconData,
                          color: selected ? const Color(0xFF8B5CF6) : MedixColors.textMuted, size: 22),
                        const SizedBox(height: 4),
                        Text(t['label'] as String,
                          style: TextStyle(fontSize: 11,
                            color: selected ? MedixColors.textPrimary : MedixColors.textMuted)),
                      ]),
                    ),
                  );
                },
              ),
            ),

            const SizedBox(height: 20),

            // ── Upload area ───────────────────────────────
            GestureDetector(
              onTap: () => _showSourcePicker(context),
              child: Container(
                width: double.infinity,
                height: _selectedImage == null ? 200 : null,
                decoration: BoxDecoration(
                  color: MedixColors.bgSurface,
                  borderRadius: BorderRadius.circular(16),
                  border: Border.all(
                    color: _selectedImage != null ? const Color(0xFF8B5CF6) : MedixColors.border,
                    style: _selectedImage == null ? BorderStyle.solid : BorderStyle.solid,
                  ),
                ),
                child: _selectedImage == null
                  ? const Column(mainAxisAlignment: MainAxisAlignment.center, children: [
                      Icon(Icons.add_photo_alternate_outlined,
                        color: MedixColors.textMuted, size: 48),
                      SizedBox(height: 12),
                      Text('Toca para cargar imagen médica',
                        style: TextStyle(color: MedixColors.textSecondary)),
                      SizedBox(height: 4),
                      Text('JPG, PNG, WEBP — Máx 10MB',
                        style: TextStyle(color: MedixColors.textMuted, fontSize: 12)),
                    ])
                  : ClipRRect(
                      borderRadius: BorderRadius.circular(14),
                      child: Image.network(_selectedImage!.path, fit: BoxFit.contain),
                    ),
              ),
            ),

            const SizedBox(height: 16),

            // ── Botón analizar ───────────────────────────
            ElevatedButton.icon(
              onPressed: _selectedImage == null || _analyzing ? null : _analyze,
              icon: _analyzing
                ? const SizedBox(width: 18, height: 18,
                    child: CircularProgressIndicator(color: Colors.white, strokeWidth: 2))
                : const Icon(Icons.auto_fix_high),
              label: Text(_analyzing ? 'Analizando con IA...' : 'Analizar con Claude Vision'),
              style: ElevatedButton.styleFrom(
                backgroundColor: const Color(0xFF8B5CF6),
              ),
            ),

            // ── Resultado ────────────────────────────────
            if (_result != null) ...[
              const SizedBox(height: 24),
              Row(children: [
                const Text('Resultado del análisis',
                  style: TextStyle(fontSize: 16, fontWeight: FontWeight.w600)),
                const Spacer(),
                UrgencyBadge(level: _result!['urgency_level'] ?? 'low'),
              ]),
              const SizedBox(height: 14),

              _ResultSection(title: '📋 Resumen', content: _result!['summary'] ?? ''),
              const SizedBox(height: 12),
              _ResultSection(title: '🔍 Hallazgos', content: _result!['findings'] ?? ''),
              const SizedBox(height: 12),
              _ResultSection(title: '💊 Recomendaciones', content: _result!['recommendations'] ?? ''),

              const SizedBox(height: 12),
              Container(
                padding: const EdgeInsets.all(12),
                decoration: BoxDecoration(
                  color: MedixColors.warning.withOpacity(0.1),
                  borderRadius: BorderRadius.circular(10),
                  border: Border.all(color: MedixColors.warning.withOpacity(0.3)),
                ),
                child: const Text(
                  '⚠️ Este análisis es orientativo. El diagnóstico final requiere evaluación clínica por un médico.',
                  style: TextStyle(fontSize: 11, color: MedixColors.warning),
                ),
              ),
            ],
          ],
        ),
      ),
    );
  }

  void _showSourcePicker(BuildContext context) {
    showModalBottomSheet(
      context: context,
      backgroundColor: MedixColors.bgSurface,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(20))),
      builder: (_) => Padding(
        padding: const EdgeInsets.all(20),
        child: Column(mainAxisSize: MainAxisSize.min, children: [
          ListTile(
            leading: const Icon(Icons.camera_alt_outlined, color: MedixColors.blue),
            title: const Text('Tomar foto'),
            onTap: () { Navigator.pop(context); _pickImage(ImageSource.camera); },
          ),
          ListTile(
            leading: const Icon(Icons.photo_library_outlined, color: MedixColors.blue),
            title: const Text('Galería'),
            onTap: () { Navigator.pop(context); _pickImage(ImageSource.gallery); },
          ),
        ]),
      ),
    );
  }
}

class _ResultSection extends StatelessWidget {
  final String title;
  final String content;
  const _ResultSection({required this.title, required this.content});

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: MedixColors.bgSurface,
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: MedixColors.border),
      ),
      child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
        Text(title, style: const TextStyle(fontWeight: FontWeight.w600, fontSize: 13)),
        const SizedBox(height: 8),
        MarkdownBody(
          data: content,
          styleSheet: MarkdownStyleSheet(
            p: const TextStyle(color: MedixColors.textSecondary, fontSize: 13, height: 1.5),
          ),
        ),
      ]),
    );
  }
}
