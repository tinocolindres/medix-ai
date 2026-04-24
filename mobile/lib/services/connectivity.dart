import 'dart:async';
import 'package:connectivity_plus/connectivity_plus.dart';
import 'package:flutter/material.dart';
import '../theme.dart';

class ConnectivityService {
  static final ConnectivityService _instance = ConnectivityService._internal();
  factory ConnectivityService() => _instance;
  ConnectivityService._internal();

  final _connectivity = Connectivity();
  final _controller = StreamController<bool>.broadcast();
  bool _isOnline = true;

  bool get isOnline => _isOnline;
  Stream<bool> get onConnectivityChanged => _controller.stream;

  Future<void> init() async {
    final result = await _connectivity.checkConnectivity();
    _isOnline = result != ConnectivityResult.none;

    _connectivity.onConnectivityChanged.listen((result) {
      final online = result != ConnectivityResult.none;
      if (online != _isOnline) {
        _isOnline = online;
        _controller.add(online);
      }
    });
  }

  void dispose() => _controller.close();
}

/// Banner de estado offline — muéstralo en el Scaffold
class OfflineBanner extends StatefulWidget {
  const OfflineBanner({super.key});

  @override
  State<OfflineBanner> createState() => _OfflineBannerState();
}

class _OfflineBannerState extends State<OfflineBanner> {
  bool _offline = false;
  StreamSubscription<bool>? _sub;

  @override
  void initState() {
    super.initState();
    _offline = !ConnectivityService().isOnline;
    _sub = ConnectivityService().onConnectivityChanged.listen((online) {
      setState(() => _offline = !online);
    });
  }

  @override
  void dispose() {
    _sub?.cancel();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    if (!_offline) return const SizedBox.shrink();
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.symmetric(vertical: 8, horizontal: 16),
      color: MedixColors.warning.withOpacity(0.15),
      child: const Row(children: [
        Icon(Icons.wifi_off, color: MedixColors.warning, size: 16),
        SizedBox(width: 8),
        Expanded(
          child: Text(
            'Sin conexión — Modo Guardia disponible offline',
            style: TextStyle(color: MedixColors.warning, fontSize: 12),
          ),
        ),
      ]),
    );
  }
}
