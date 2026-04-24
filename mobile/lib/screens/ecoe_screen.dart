import 'package:flutter/material.dart';
import 'package:flutter_markdown/flutter_markdown.dart';
import '../theme.dart';
import '../services/api.dart';

class ECOEScreen extends StatefulWidget {
  const ECOEScreen({super.key});

  @override
  State<ECOEScreen> createState() => _ECOEScreenState();
}

class _ECOEScreenState extends State<ECOEScreen> {
  final _msgCtrl = TextEditingController();
  final _scrollCtrl = ScrollController();

  final _cases = [
    {'id': 'ecoe_001', 'title': 'Dolor Abdominal Agudo',   'hint': 'Paciente con dolor FID', 'color': MedixColors.danger,  'icon': '🏥'},
    {'id': 'ecoe_002', 'title': 'Fiebre + Rash',           'hint': 'Paciente con dengue',     'color': MedixColors.warning, 'icon': '🦟'},
    {'id': 'ecoe_003', 'title': 'Dolor Torácico',          'hint': 'Posible IAM',             'color': MedixColors.danger,  'icon': '❤️'},
  ];

  String? _activeCaseId;
  String? _caseTitle;
  String? _systemPrompt;
  String? _sessionId;
  bool _loading = false;
  bool _starting = false;

  List<Map<String, String>> _messages = [];

  Future<void> _startCase(Map<String, dynamic> caseData) async {
    setState(() { _starting = true; _messages = []; _sessionId = null; });

    try {
      final result = await ApiService().startECOE(caseData['id'] as String);
      setState(() {
        _activeCaseId = caseData['id'] as String;
        _caseTitle = caseData['title'] as String;
        _systemPrompt = result['system_prompt'];
        _messages = [
          {'role': 'patient', 'text': result['patient_opening'] ?? ''},
        ];
      });
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Error: $e'), backgroundColor: MedixColors.danger),
        );
      }
    } finally {
      setState(() => _starting = false);
    }
  }

  Future<void> _sendMessage() async {
    final text = _msgCtrl.text.trim();
    if (text.isEmpty || _loading) return;

    setState(() {
      _messages.add({'role': 'doctor', 'text': text});
      _loading = true;
    });
    _msgCtrl.clear();
    _scrollToBottom();

    try {
      final result = await ApiService().sendChatMessage(
        message: text,
        sessionId: _sessionId,
        mode: 'ecoe_simulator',
      );
      setState(() {
        _sessionId = result['session_id'];
        _messages.add({'role': 'patient', 'text': result['response'] ?? ''});
      });
    } catch (e) {
      setState(() {
        _messages.add({'role': 'system', 'text': '⚠️ Error de conexión.'});
      });
    } finally {
      setState(() => _loading = false);
      _scrollToBottom();
    }
  }

  void _scrollToBottom() {
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (_scrollCtrl.hasClients) {
        _scrollCtrl.animateTo(
          _scrollCtrl.position.maxScrollExtent,
          duration: const Duration(milliseconds: 300),
          curve: Curves.easeOut,
        );
      }
    });
  }

  void _endSession() {
    setState(() {
      _activeCaseId = null;
      _messages = [];
      _sessionId = null;
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Row(children: [
          Container(
            padding: const EdgeInsets.all(6),
            decoration: BoxDecoration(
              color: MedixColors.warning.withOpacity(0.15),
              borderRadius: BorderRadius.circular(8),
            ),
            child: const Icon(Icons.theater_comedy_outlined,
              color: MedixColors.warning, size: 20),
          ),
          const SizedBox(width: 10),
          Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
            const Text('Simulador ECOE', style: TextStyle(fontSize: 15)),
            Text(_activeCaseId != null ? _caseTitle! : 'Selecciona un caso',
              style: const TextStyle(color: MedixColors.textSecondary, fontSize: 11)),
          ]),
        ]),
        actions: [
          if (_activeCaseId != null)
            TextButton.icon(
              onPressed: _endSession,
              icon: const Icon(Icons.stop_circle_outlined, color: MedixColors.danger, size: 18),
              label: const Text('Finalizar', style: TextStyle(color: MedixColors.danger, fontSize: 12)),
            ),
        ],
      ),
      body: _activeCaseId == null ? _caseSelector() : _simulatorView(),
    );
  }

  Widget _caseSelector() {
    return SingleChildScrollView(
      padding: const EdgeInsets.all(20),
      child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
        // Banner instructivo
        Container(
          padding: const EdgeInsets.all(16),
          decoration: BoxDecoration(
            color: MedixColors.warning.withOpacity(0.1),
            borderRadius: BorderRadius.circular(14),
            border: Border.all(color: MedixColors.warning.withOpacity(0.3)),
          ),
          child: const Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
            Text('🎭 ¿Cómo funciona?',
              style: TextStyle(fontWeight: FontWeight.w700, fontSize: 14)),
            SizedBox(height: 8),
            Text(
              '1. Selecciona un caso clínico\n'
              '2. El paciente virtual te recibirá\n'
              '3. Interroga como en un ECOE/OSCE real\n'
              '4. Llega al diagnóstico para completar el caso',
              style: TextStyle(color: MedixColors.textSecondary, height: 1.6, fontSize: 13),
            ),
          ]),
        ),

        const SizedBox(height: 24),
        const Text('Casos disponibles',
          style: TextStyle(fontSize: 16, fontWeight: FontWeight.w600)),
        const SizedBox(height: 14),

        ..._cases.map((c) => Padding(
          padding: const EdgeInsets.only(bottom: 12),
          child: GestureDetector(
            onTap: _starting ? null : () => _startCase(c),
            child: Container(
              padding: const EdgeInsets.all(18),
              decoration: BoxDecoration(
                color: MedixColors.bgSurface,
                borderRadius: BorderRadius.circular(16),
                border: Border.all(color: MedixColors.border),
              ),
              child: Row(children: [
                Container(
                  width: 50, height: 50,
                  decoration: BoxDecoration(
                    color: (c['color'] as Color).withOpacity(0.15),
                    borderRadius: BorderRadius.circular(14),
                  ),
                  alignment: Alignment.center,
                  child: Text(c['icon'] as String, style: const TextStyle(fontSize: 26)),
                ),
                const SizedBox(width: 14),
                Expanded(child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                  Text(c['title'] as String,
                    style: const TextStyle(fontWeight: FontWeight.w600, fontSize: 15)),
                  const SizedBox(height: 2),
                  Text(c['hint'] as String,
                    style: const TextStyle(color: MedixColors.textSecondary, fontSize: 12)),
                ])),
                if (_starting)
                  const SizedBox(width: 20, height: 20,
                    child: CircularProgressIndicator(strokeWidth: 2, color: MedixColors.warning))
                else
                  const Icon(Icons.play_circle_outline, color: MedixColors.warning, size: 28),
              ]),
            ),
          ),
        )),
      ]),
    );
  }

  Widget _simulatorView() {
    return Column(children: [
      // Banner de caso activo
      Container(
        width: double.infinity,
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
        color: MedixColors.warning.withOpacity(0.1),
        child: Row(children: [
          const Icon(Icons.person_outline, color: MedixColors.warning, size: 16),
          const SizedBox(width: 8),
          const Text('Paciente virtual activo — ',
            style: TextStyle(color: MedixColors.warning, fontSize: 12)),
          Text(_caseTitle ?? '',
            style: const TextStyle(
              color: MedixColors.warning, fontSize: 12, fontWeight: FontWeight.w600)),
        ]),
      ),

      // Mensajes
      Expanded(
        child: ListView.builder(
          controller: _scrollCtrl,
          padding: const EdgeInsets.all(16),
          itemCount: _messages.length + (_loading ? 1 : 0),
          itemBuilder: (ctx, i) {
            if (i == _messages.length) {
              return const Padding(
                padding: EdgeInsets.only(bottom: 12),
                child: Row(children: [
                  SizedBox(width: 40, height: 40,
                    child: CircleAvatar(
                      backgroundColor: MedixColors.bgSurface,
                      child: Text('🤒', style: TextStyle(fontSize: 20)))),
                  SizedBox(width: 10),
                  Text('Pensando...', style: TextStyle(color: MedixColors.textMuted, fontSize: 13)),
                ]),
              );
            }
            final msg = _messages[i];
            final isDoctor = msg['role'] == 'doctor';

            return Padding(
              padding: const EdgeInsets.only(bottom: 14),
              child: Row(
                mainAxisAlignment: isDoctor
                  ? MainAxisAlignment.end
                  : MainAxisAlignment.start,
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  if (!isDoctor) ...[
                    const CircleAvatar(
                      radius: 18,
                      backgroundColor: MedixColors.bgSurface,
                      child: Text('🤒', style: TextStyle(fontSize: 18))),
                    const SizedBox(width: 8),
                  ],
                  Flexible(
                    child: Container(
                      padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
                      decoration: BoxDecoration(
                        color: isDoctor ? MedixColors.blue : MedixColors.bgSurface,
                        borderRadius: BorderRadius.only(
                          topLeft: const Radius.circular(16),
                          topRight: const Radius.circular(16),
                          bottomLeft: Radius.circular(isDoctor ? 16 : 4),
                          bottomRight: Radius.circular(isDoctor ? 4 : 16),
                        ),
                        border: isDoctor ? null : Border.all(color: MedixColors.border),
                      ),
                      child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                        if (!isDoctor)
                          const Text('Paciente',
                            style: TextStyle(color: MedixColors.textMuted, fontSize: 10)),
                        MarkdownBody(
                          data: msg['text'] ?? '',
                          styleSheet: MarkdownStyleSheet(
                            p: TextStyle(
                              color: isDoctor ? Colors.white : MedixColors.textPrimary,
                              height: 1.5, fontSize: 13,
                            ),
                          ),
                        ),
                      ]),
                    ),
                  ),
                  if (isDoctor) ...[
                    const SizedBox(width: 8),
                    const CircleAvatar(
                      radius: 18,
                      backgroundColor: MedixColors.blue,
                      child: Icon(Icons.person, color: Colors.white, size: 18)),
                  ],
                ],
              ),
            );
          },
        ),
      ),

      // Sugerencias rápidas
      SizedBox(
        height: 40,
        child: ListView(
          scrollDirection: Axis.horizontal,
          padding: const EdgeInsets.symmetric(horizontal: 16),
          children: [
            '¿Dónde le duele?',
            '¿Desde cuándo?',
            '¿Tiene fiebre?',
            '¿Signos vitales?',
            'Examen físico abdominal',
          ].map((q) => GestureDetector(
            onTap: () { _msgCtrl.text = q; _sendMessage(); },
            child: Container(
              margin: const EdgeInsets.only(right: 8),
              padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
              decoration: BoxDecoration(
                color: MedixColors.bgSurface,
                borderRadius: BorderRadius.circular(16),
                border: Border.all(color: MedixColors.border),
              ),
              child: Text(q, style: const TextStyle(
                color: MedixColors.textSecondary, fontSize: 12)),
            ),
          )).toList(),
        ),
      ),

      const SizedBox(height: 8),

      // Input
      Container(
        padding: const EdgeInsets.fromLTRB(16, 8, 16, 16),
        decoration: const BoxDecoration(
          color: MedixColors.bgSurface,
          border: Border(top: BorderSide(color: MedixColors.border)),
        ),
        child: Row(children: [
          Expanded(
            child: TextField(
              controller: _msgCtrl,
              maxLines: 3,
              minLines: 1,
              decoration: const InputDecoration(
                hintText: 'Pregunta al paciente...',
                contentPadding: EdgeInsets.symmetric(horizontal: 14, vertical: 10),
              ),
              onSubmitted: (_) => _sendMessage(),
            ),
          ),
          const SizedBox(width: 10),
          GestureDetector(
            onTap: _loading ? null : _sendMessage,
            child: Container(
              width: 44, height: 44,
              decoration: BoxDecoration(
                color: _loading ? MedixColors.border : MedixColors.warning,
                borderRadius: BorderRadius.circular(12),
              ),
              child: const Icon(Icons.send_rounded, color: Colors.white, size: 20),
            ),
          ),
        ]),
      ),
    ]);
  }
}
