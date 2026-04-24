import 'package:flutter/material.dart';
import 'package:flutter_markdown/flutter_markdown.dart';
import '../theme.dart';
import '../services/api.dart';

class ChatScreen extends StatefulWidget {
  const ChatScreen({super.key});

  @override
  State<ChatScreen> createState() => _ChatScreenState();
}

class _ChatScreenState extends State<ChatScreen> {
  final _msgCtrl = TextEditingController();
  final _scrollCtrl = ScrollController();
  final List<_Message> _messages = [];
  String? _sessionId;
  bool _loading = false;
  String _mode = 'chat';

  Future<void> _send() async {
    final text = _msgCtrl.text.trim();
    if (text.isEmpty || _loading) return;

    setState(() {
      _messages.add(_Message(text: text, isUser: true));
      _loading = true;
    });
    _msgCtrl.clear();
    _scrollToBottom();

    try {
      final response = await ApiService().sendChatMessage(
        message: text,
        sessionId: _sessionId,
        mode: _mode,
      );
      setState(() {
        _sessionId = response['session_id'];
        _messages.add(_Message(
          text: response['response'],
          isUser: false,
          tokensUsed: response['tokens_used'],
        ));
      });
    } catch (e) {
      setState(() {
        _messages.add(const _Message(
          text: '⚠️ Error de conexión. Verifica tu internet.',
          isUser: false,
          isError: true,
        ));
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

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Row(children: [
          Container(
            width: 34, height: 34,
            decoration: BoxDecoration(
              color: MedixColors.blue.withOpacity(0.15),
              borderRadius: BorderRadius.circular(10),
            ),
            child: const Icon(Icons.psychology, color: MedixColors.blue, size: 20),
          ),
          const SizedBox(width: 10),
          const Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
            Text('Chat IA Médico', style: TextStyle(fontSize: 15)),
            Text('Conectado', style: TextStyle(color: MedixColors.success, fontSize: 11)),
          ]),
        ]),
        actions: [
          // Selector de modo
          PopupMenuButton<String>(
            icon: const Icon(Icons.tune_outlined),
            color: MedixColors.bgSurface,
            onSelected: (v) => setState(() {
              _mode = v;
              _sessionId = null;
              _messages.clear();
            }),
            itemBuilder: (_) => [
              const PopupMenuItem(value: 'chat', child: Text('💬 Chat General')),
              const PopupMenuItem(value: 'guardia', child: Text('🏥 Modo Guardia')),
              const PopupMenuItem(value: 'soap_dictation', child: Text('📝 Dictado SOAP')),
              const PopupMenuItem(value: 'ecoe_simulator', child: Text('🎭 Simulador ECOE')),
            ],
          ),
        ],
      ),
      body: Column(
        children: [
          // ── Banner de modo activo ─────────────────────────
          if (_mode != 'chat')
            Container(
              width: double.infinity,
              padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
              color: MedixColors.bgSurface,
              child: Text(
                _modeLabel,
                style: const TextStyle(color: MedixColors.textSecondary, fontSize: 12),
                textAlign: TextAlign.center,
              ),
            ),

          // ── Mensajes ──────────────────────────────────────
          Expanded(
            child: _messages.isEmpty
              ? _EmptyState(mode: _mode)
              : ListView.builder(
                  controller: _scrollCtrl,
                  padding: const EdgeInsets.all(16),
                  itemCount: _messages.length + (_loading ? 1 : 0),
                  itemBuilder: (ctx, i) {
                    if (i == _messages.length) return const _TypingIndicator();
                    return _MessageBubble(message: _messages[i]);
                  },
                ),
          ),

          // ── Input ─────────────────────────────────────────
          Container(
            padding: const EdgeInsets.fromLTRB(16, 12, 16, 16),
            decoration: const BoxDecoration(
              color: MedixColors.bgSurface,
              border: Border(top: BorderSide(color: MedixColors.border)),
            ),
            child: Row(children: [
              Expanded(
                child: TextField(
                  controller: _msgCtrl,
                  maxLines: 4,
                  minLines: 1,
                  textInputAction: TextInputAction.send,
                  onSubmitted: (_) => _send(),
                  decoration: InputDecoration(
                    hintText: _inputHint,
                    contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
                  ),
                ),
              ),
              const SizedBox(width: 10),
              GestureDetector(
                onTap: _send,
                child: Container(
                  width: 46, height: 46,
                  decoration: BoxDecoration(
                    color: _loading ? MedixColors.border : MedixColors.blue,
                    borderRadius: BorderRadius.circular(12),
                  ),
                  child: Icon(
                    _loading ? Icons.hourglass_empty : Icons.send_rounded,
                    color: Colors.white, size: 20,
                  ),
                ),
              ),
            ]),
          ),
        ],
      ),
    );
  }

  String get _modeLabel => switch (_mode) {
    'guardia'        => '🏥 MODO GUARDIA — Respuestas rápidas para emergencias',
    'soap_dictation' => '📝 DICTADO SOAP — Dicta y genera nota de evolución estructurada',
    'ecoe_simulator' => '🎭 SIMULADOR ECOE — Practica con pacientes virtuales',
    _                => '',
  };

  String get _inputHint => switch (_mode) {
    'guardia'        => 'Describe el caso de emergencia...',
    'soap_dictation' => 'Dicta la nota clínica...',
    'ecoe_simulator' => 'Interroga al paciente...',
    _                => 'Haz una consulta médica...',
  };
}

// ── Componentes ─────────────────────────────────────────────────
class _Message {
  final String text;
  final bool isUser;
  final bool isError;
  final int? tokensUsed;
  const _Message({required this.text, required this.isUser, this.isError = false, this.tokensUsed});
}

class _MessageBubble extends StatelessWidget {
  final _Message message;
  const _MessageBubble({super.key, required this.message});

  @override
  Widget build(BuildContext context) {
    if (message.isUser) {
      return Align(
        alignment: Alignment.centerRight,
        child: Container(
          margin: const EdgeInsets.only(bottom: 12, left: 60),
          padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
          decoration: BoxDecoration(
            color: MedixColors.blue,
            borderRadius: const BorderRadius.only(
              topLeft: Radius.circular(16), topRight: Radius.circular(16),
              bottomLeft: Radius.circular(16), bottomRight: Radius.circular(4),
            ),
          ),
          child: Text(message.text, style: const TextStyle(color: Colors.white)),
        ),
      );
    }

    return Align(
      alignment: Alignment.centerLeft,
      child: Container(
        margin: const EdgeInsets.only(bottom: 12, right: 40),
        padding: const EdgeInsets.all(16),
        decoration: BoxDecoration(
          color: message.isError
            ? MedixColors.danger.withOpacity(0.1)
            : MedixColors.bgSurface,
          borderRadius: const BorderRadius.only(
            topLeft: Radius.circular(4), topRight: Radius.circular(16),
            bottomLeft: Radius.circular(16), bottomRight: Radius.circular(16),
          ),
          border: Border.all(
            color: message.isError ? MedixColors.danger.withOpacity(0.3) : MedixColors.border,
          ),
        ),
        child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
          MarkdownBody(
            data: message.text,
            styleSheet: MarkdownStyleSheet(
              p: const TextStyle(color: MedixColors.textPrimary, height: 1.5),
              strong: const TextStyle(color: MedixColors.textPrimary, fontWeight: FontWeight.w600),
              listBullet: const TextStyle(color: MedixColors.textSecondary),
            ),
          ),
          if (message.tokensUsed != null) ...[
            const SizedBox(height: 8),
            Text('${message.tokensUsed} tokens',
              style: const TextStyle(color: MedixColors.textMuted, fontSize: 10)),
          ],
        ]),
      ),
    );
  }
}

class _TypingIndicator extends StatelessWidget {
  const _TypingIndicator();
  @override
  Widget build(BuildContext context) {
    return Align(
      alignment: Alignment.centerLeft,
      child: Container(
        margin: const EdgeInsets.only(bottom: 12),
        padding: const EdgeInsets.all(14),
        decoration: BoxDecoration(
          color: MedixColors.bgSurface,
          borderRadius: BorderRadius.circular(14),
          border: Border.all(color: MedixColors.border),
        ),
        child: Row(mainAxisSize: MainAxisSize.min, children: [
          const SizedBox(width: 16, height: 16,
            child: CircularProgressIndicator(color: MedixColors.blue, strokeWidth: 2)),
          const SizedBox(width: 10),
          const Text('Medix AI procesando...',
            style: TextStyle(color: MedixColors.textSecondary, fontSize: 13)),
        ]),
      ),
    );
  }
}

class _EmptyState extends StatelessWidget {
  final String mode;
  const _EmptyState({required this.mode});

  @override
  Widget build(BuildContext context) {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(32),
        child: Column(mainAxisAlignment: MainAxisAlignment.center, children: [
          Container(
            padding: const EdgeInsets.all(24),
            decoration: BoxDecoration(
              color: MedixColors.blue.withOpacity(0.1),
              shape: BoxShape.circle,
            ),
            child: const Icon(Icons.psychology, color: MedixColors.blue, size: 48),
          ),
          const SizedBox(height: 20),
          const Text('Medix AI listo',
            style: TextStyle(fontSize: 18, fontWeight: FontWeight.w600)),
          const SizedBox(height: 8),
          const Text('Consulta sobre medicamentos, diagnósticos, protocolos o estudios de laboratorio.',
            textAlign: TextAlign.center,
            style: TextStyle(color: MedixColors.textSecondary)),
        ]),
      ),
    );
  }
}
