import 'package:flutter/material.dart';
import '../theme.dart';
import '../services/api.dart';

/// Widget de feedback rápido flotante — se muestra después de usar un módulo
class FeedbackWidget extends StatefulWidget {
  final String module;
  final VoidCallback onDismiss;

  const FeedbackWidget({
    super.key,
    required this.module,
    required this.onDismiss,
  });

  @override
  State<FeedbackWidget> createState() => _FeedbackWidgetState();
}

class _FeedbackWidgetState extends State<FeedbackWidget> {
  int _rating = 0;
  final _msgCtrl = TextEditingController();
  bool _submitted = false;
  bool _loading = false;

  Future<void> _submit() async {
    if (_rating == 0) return;
    setState(() => _loading = true);
    try {
      await ApiService().submitFeedback(
        rating: _rating,
        module: widget.module,
        message: _msgCtrl.text.trim().isEmpty ? null : _msgCtrl.text.trim(),
      );
      setState(() => _submitted = true);
      await Future.delayed(const Duration(seconds: 2));
      widget.onDismiss();
    } catch (_) {
      widget.onDismiss();
    }
  }

  @override
  Widget build(BuildContext context) {
    return Container(
      margin: const EdgeInsets.all(16),
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        color: MedixColors.bgSurface,
        borderRadius: BorderRadius.circular(20),
        border: Border.all(color: MedixColors.border),
        boxShadow: [
          BoxShadow(color: Colors.black.withOpacity(0.3), blurRadius: 20),
        ],
      ),
      child: _submitted
          ? const Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                Text('🎉', style: TextStyle(fontSize: 36)),
                SizedBox(height: 8),
                Text('¡Gracias por tu feedback!',
                  style: TextStyle(fontWeight: FontWeight.w600)),
                SizedBox(height: 4),
                Text('Nos ayuda a mejorar Medix AI',
                  style: TextStyle(color: MedixColors.textSecondary, fontSize: 13)),
              ],
            )
          : Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    Text(
                      '¿Cómo fue tu experiencia con ${widget.module}?',
                      style: const TextStyle(fontWeight: FontWeight.w600, fontSize: 14),
                    ),
                    GestureDetector(
                      onTap: widget.onDismiss,
                      child: const Icon(Icons.close, color: MedixColors.textMuted, size: 20),
                    ),
                  ],
                ),
                const SizedBox(height: 16),

                // Stars
                Row(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: List.generate(5, (i) {
                    final filled = i < _rating;
                    return GestureDetector(
                      onTap: () => setState(() => _rating = i + 1),
                      child: Padding(
                        padding: const EdgeInsets.symmetric(horizontal: 6),
                        child: Icon(
                          filled ? Icons.star_rounded : Icons.star_outline_rounded,
                          color: filled ? MedixColors.warning : MedixColors.border,
                          size: 36,
                        ),
                      ),
                    );
                  }),
                ),

                if (_rating > 0) ...[
                  const SizedBox(height: 14),
                  Text(
                    _ratingLabel,
                    style: TextStyle(color: _ratingColor, fontSize: 13),
                  ),
                  const SizedBox(height: 12),
                  TextField(
                    controller: _msgCtrl,
                    maxLines: 2,
                    decoration: const InputDecoration(
                      hintText: 'Comentario opcional...',
                      contentPadding: EdgeInsets.all(12),
                    ),
                  ),
                  const SizedBox(height: 12),
                  ElevatedButton(
                    onPressed: _loading ? null : _submit,
                    child: _loading
                      ? const SizedBox(width: 16, height: 16,
                          child: CircularProgressIndicator(color: Colors.white, strokeWidth: 2))
                      : const Text('Enviar feedback'),
                  ),
                ],
              ],
            ),
    );
  }

  String get _ratingLabel => switch (_rating) {
    1 => 'Necesita mejorar mucho',
    2 => 'Por debajo de lo esperado',
    3 => 'Cumple las expectativas',
    4 => 'Muy bueno',
    5 => '¡Excelente! 🎉',
    _ => '',
  };

  Color get _ratingColor => switch (_rating) {
    1 || 2 => MedixColors.danger,
    3      => MedixColors.warning,
    _      => MedixColors.success,
  };
}

/// Helper para mostrar el feedback como bottom sheet
void showFeedbackSheet(BuildContext context, String module) {
  // No molestar al usuario más de una vez por sesión por módulo
  showModalBottomSheet(
    context: context,
    backgroundColor: Colors.transparent,
    isScrollControlled: true,
    builder: (_) => FeedbackWidget(
      module: module,
      onDismiss: () => Navigator.pop(context),
    ),
  );
}
