import 'package:flutter_local_notifications/flutter_local_notifications.dart';

class NotificationService {
  static final NotificationService _instance = NotificationService._internal();
  factory NotificationService() => _instance;
  NotificationService._internal();

  final _plugin = FlutterLocalNotificationsPlugin();
  bool _initialized = false;

  Future<void> init() async {
    if (_initialized) return;

    const androidSettings = AndroidInitializationSettings('@mipmap/ic_launcher');
    const iosSettings = DarwinInitializationSettings(
      requestAlertPermission: true,
      requestBadgePermission: true,
      requestSoundPermission: true,
    );

    await _plugin.initialize(
      const InitializationSettings(android: androidSettings, iOS: iosSettings),
    );

    _initialized = true;
  }

  // ── Notificación scan completado ──────────────────────────────
  Future<void> notifyScanComplete({
    required String urgencyLevel,
    required String summary,
  }) async {
    final isUrgent = urgencyLevel == 'critical' || urgencyLevel == 'high';

    await _plugin.show(
      1001,
      isUrgent ? '⚠️ MedScan — Hallazgo Urgente' : '✅ MedScan Completado',
      summary.length > 80 ? '${summary.substring(0, 80)}...' : summary,
      NotificationDetails(
        android: AndroidNotificationDetails(
          'medscan_channel',
          'MedScan Resultados',
          channelDescription: 'Resultados de análisis de imágenes médicas',
          importance: isUrgent ? Importance.max : Importance.high,
          priority: isUrgent ? Priority.max : Priority.high,
          color: isUrgent
            ? const Color(0xFFEF4444)
            : const Color(0xFF22C55E),
          enableLights: isUrgent,
          playSound: true,
        ),
        iOS: const DarwinNotificationDetails(
          presentAlert: true,
          presentBadge: true,
          presentSound: true,
        ),
      ),
    );
  }

  // ── Recordatorio de límite de plan ────────────────────────────
  Future<void> notifyRateLimitWarning({
    required int used,
    required int limit,
    required String feature,
  }) async {
    if (used < limit * 0.8) return; // Solo notificar al 80% del límite

    await _plugin.show(
      2001,
      '📊 Límite de $feature',
      'Usaste $used de $limit $feature disponibles hoy.',
      const NotificationDetails(
        android: AndroidNotificationDetails(
          'limits_channel',
          'Límites de uso',
          channelDescription: 'Avisos de límites de plan',
          importance: Importance.defaultImportance,
        ),
      ),
    );
  }

  // ── Notificación modo guardia (turno nocturno) ─────────────────
  Future<void> scheduleGuardiaReminder() async {
    // Recordatorio de inicio de turno nocturno (20:00)
    await _plugin.show(
      3001,
      '🏥 Medix AI — Modo Guardia',
      'Calculadoras offline disponibles para tu turno nocturno.',
      const NotificationDetails(
        android: AndroidNotificationDetails(
          'guardia_channel',
          'Recordatorio Guardia',
          channelDescription: 'Recordatorios para turno de guardia',
          importance: Importance.low,
        ),
      ),
    );
  }

  // ── Cancelar todas ────────────────────────────────────────────
  Future<void> cancelAll() async {
    await _plugin.cancelAll();
  }
}
