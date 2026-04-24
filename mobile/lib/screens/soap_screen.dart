import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_markdown/flutter_markdown.dart';
import 'package:speech_to_text/speech_to_text.dart';
import '../theme.dart';
import '../services/api.dart';

class SOAPScreen extends StatefulWidget {
  const SOAPScreen({super.key});

  @override
  State<SOAPScreen> createState() => _SOAPScreenState();
}

class _SOAPScreenState extends State<SOAPScreen> {
  final _stt = SpeechToText();
  final _textCtrl = TextEditingController();
  bool _sttAvailable = false;
  bool _listening = false;
  bool _generating = false;
  String? _soapNote;

  @override
  void initState() {
    super.initState();
    _initSpeech();
  }

  Future<void> _initSpeech() async {
    final available = await _stt.initialize(
      onStatus: (status) {
        if (status == 'done' || status == 'notListening') {
          setState(() => _listening = false);
        }
      },
    );
    setState(() => _sttAvailable = available);
  }

  Future<void> _toggleListening() async {
    if (_listening) {
      await _stt.stop();
      setState(() => _listening = false);
      return;
    }

    await _stt.listen(
      localeId: 'es_HN',
      onResult: (result) {
        setState(() {
          _textCtrl.text = result.recognizedWords;
          _listening = result.hasConfidenceRating ? !result.finalResult : _listening;
        });
      },
    );
    setState(() => _listening = true);
  }

  Future<void> _generateSOAP() async {
    if (_textCtrl.text.trim().isEmpty) return;
    setState(() { _generating = true; _soapNote = null; });

    try {
      final result = await ApiService().generateSoapNote(_textCtrl.text.trim());
      setState(() => _soapNote = result['soap_note']);
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Error al generar nota. Requiere plan Pro.'),
            backgroundColor: MedixColors.danger),
        );
      }
    } finally {
      setState(() => _generating = false);
    }
  }

  void _copyNote() {
    if (_soapNote != null) {
      Clipboard.setData(ClipboardData(text: _soapNote!));
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('✅ Nota copiada al portapapeles'),
          backgroundColor: MedixColors.success),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('📝 Dictado SOAP'),
        actions: [
          if (_soapNote != null)
            IconButton(
              icon: const Icon(Icons.copy_outlined),
              tooltip: 'Copiar nota',
              onPressed: _copyNote,
            ),
        ],
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(20),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // ── Info header ───────────────────────────────
            Container(
              padding: const EdgeInsets.all(14),
              decoration: BoxDecoration(
                color: MedixColors.success.withOpacity(0.1),
                borderRadius: BorderRadius.circular(12),
                border: Border.all(color: MedixColors.success.withOpacity(0.3)),
              ),
              child: const Row(children: [
                Icon(Icons.mic, color: MedixColors.success, size: 20),
                SizedBox(width: 10),
                Expanded(child: Text(
                  'Dicta el caso clínico en lenguaje natural. La IA lo transforma en nota SOAP estructurada.',
                  style: TextStyle(color: MedixColors.success, fontSize: 13),
                )),
              ]),
            ),

            const SizedBox(height: 20),

            // ── Área de dictado ───────────────────────────
            const Text('Dictado clínico', style: TextStyle(fontWeight: FontWeight.w600)),
            const SizedBox(height: 8),

            TextField(
              controller: _textCtrl,
              maxLines: 8,
              decoration: InputDecoration(
                hintText: 'Paciente masculino de 35 años llega con dolor abdominal...',
                alignLabelWithHint: true,
                suffixIcon: _sttAvailable
                  ? Padding(
                      padding: const EdgeInsets.all(8),
                      child: IconButton(
                        icon: Icon(
                          _listening ? Icons.stop_circle : Icons.mic,
                          color: _listening ? MedixColors.danger : MedixColors.blue,
                          size: 28,
                        ),
                        onPressed: _toggleListening,
                      ),
                    )
                  : null,
              ),
            ),

            // ── Indicador de escucha activa ───────────────
            if (_listening) ...[
              const SizedBox(height: 10),
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 8),
                decoration: BoxDecoration(
                  color: MedixColors.danger.withOpacity(0.1),
                  borderRadius: BorderRadius.circular(8),
                ),
                child: const Row(children: [
                  SizedBox(width: 16, height: 16,
                    child: CircularProgressIndicator(color: MedixColors.danger, strokeWidth: 2)),
                  SizedBox(width: 10),
                  Text('Escuchando... Habla claramente',
                    style: TextStyle(color: MedixColors.danger, fontSize: 13)),
                ]),
              ),
            ],

            const SizedBox(height: 16),

            // ── Ejemplo rápido ────────────────────────────
            GestureDetector(
              onTap: () {
                _textCtrl.text = 'Paciente masculino 40 años refiere dolor en fosa ilíaca derecha '
                  'desde hace 18 horas, comenzó periumbilical y migró a FID, fiebre de 38.5, '
                  'náuseas, vómito x1, signo de McBurney positivo, rebote positivo, peristalsis '
                  'disminuida, leucocitos 15000. Plan: analgesia, ayuno, cirugía esta noche.';
                setState(() {});
              },
              child: const Text('📋 Cargar ejemplo',
                style: TextStyle(color: MedixColors.blue, fontSize: 13, decoration: TextDecoration.underline)),
            ),

            const SizedBox(height: 20),

            // ── Botón generar ─────────────────────────────
            ElevatedButton.icon(
              onPressed: _textCtrl.text.trim().isEmpty || _generating ? null : _generateSOAP,
              icon: _generating
                ? const SizedBox(width: 18, height: 18,
                    child: CircularProgressIndicator(color: Colors.white, strokeWidth: 2))
                : const Icon(Icons.auto_awesome),
              label: Text(_generating ? 'Generando nota SOAP...' : 'Generar Nota SOAP'),
              style: ElevatedButton.styleFrom(backgroundColor: MedixColors.success),
            ),

            // ── Resultado SOAP ────────────────────────────
            if (_soapNote != null) ...[
              const SizedBox(height: 24),
              Row(children: [
                const Text('Nota SOAP generada',
                  style: TextStyle(fontSize: 16, fontWeight: FontWeight.w600)),
                const Spacer(),
                TextButton.icon(
                  onPressed: _copyNote,
                  icon: const Icon(Icons.copy, size: 16),
                  label: const Text('Copiar'),
                ),
              ]),
              const SizedBox(height: 10),
              Container(
                padding: const EdgeInsets.all(16),
                decoration: BoxDecoration(
                  color: MedixColors.bgSurface,
                  borderRadius: BorderRadius.circular(14),
                  border: Border.all(color: MedixColors.success.withOpacity(0.4)),
                ),
                child: MarkdownBody(
                  data: _soapNote!,
                  styleSheet: MarkdownStyleSheet(
                    h3: const TextStyle(color: MedixColors.blue, fontSize: 14, fontWeight: FontWeight.w700),
                    p: const TextStyle(color: MedixColors.textPrimary, height: 1.6),
                    strong: const TextStyle(color: MedixColors.textPrimary, fontWeight: FontWeight.w600),
                  ),
                ),
              ),
              const SizedBox(height: 8),
              const Text('Lista para copiar al expediente médico',
                style: TextStyle(color: MedixColors.textMuted, fontSize: 11)),
            ],
          ],
        ),
      ),
    );
  }
}
