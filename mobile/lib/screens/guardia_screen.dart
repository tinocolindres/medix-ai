import 'package:flutter/material.dart';
import '../theme.dart';

class GuardiaScreen extends StatefulWidget {
  const GuardiaScreen({super.key});

  @override
  State<GuardiaScreen> createState() => _GuardiaScreenState();
}

class _GuardiaScreenState extends State<GuardiaScreen> {
  int _selectedCalc = 0;

  final _calcs = [
    'Holiday-Segar', 'Glasgow', 'APGAR', 'Dosis Pediátricas', 'Silverman', 'Shock Index',
  ];

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Row(children: [
          Container(
            padding: const EdgeInsets.all(6),
            decoration: BoxDecoration(
              color: MedixColors.danger.withOpacity(0.15),
              borderRadius: BorderRadius.circular(8),
            ),
            child: const Icon(Icons.local_hospital_rounded, color: MedixColors.danger, size: 20),
          ),
          const SizedBox(width: 10),
          const Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
            Text('Modo Guardia', style: TextStyle(fontSize: 15)),
            Text('100% Offline', style: TextStyle(color: MedixColors.success, fontSize: 11)),
          ]),
        ]),
      ),
      body: Column(
        children: [
          // ── Banner offline ────────────────────────────────
          Container(
            width: double.infinity,
            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
            color: MedixColors.danger.withOpacity(0.1),
            child: const Row(children: [
              Icon(Icons.wifi_off, color: MedixColors.danger, size: 16),
              SizedBox(width: 8),
              Text('Calculadoras activas sin internet — Ideal para zonas rurales y turnos nocturnos',
                style: TextStyle(color: MedixColors.danger, fontSize: 12)),
            ]),
          ),

          // ── Selector de calculadora ───────────────────────
          SizedBox(
            height: 48,
            child: ListView.separated(
              scrollDirection: Axis.horizontal,
              padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
              itemCount: _calcs.length,
              separatorBuilder: (_, __) => const SizedBox(width: 8),
              itemBuilder: (ctx, i) {
                final sel = _selectedCalc == i;
                return GestureDetector(
                  onTap: () => setState(() => _selectedCalc = i),
                  child: Container(
                    padding: const EdgeInsets.symmetric(horizontal: 14),
                    decoration: BoxDecoration(
                      color: sel ? MedixColors.danger : MedixColors.bgSurface,
                      borderRadius: BorderRadius.circular(20),
                      border: Border.all(color: sel ? MedixColors.danger : MedixColors.border),
                    ),
                    alignment: Alignment.center,
                    child: Text(_calcs[i],
                      style: TextStyle(
                        color: sel ? Colors.white : MedixColors.textSecondary,
                        fontSize: 13, fontWeight: sel ? FontWeight.w600 : FontWeight.normal,
                      )),
                  ),
                );
              },
            ),
          ),

          // ── Calculadora activa ────────────────────────────
          Expanded(
            child: SingleChildScrollView(
              padding: const EdgeInsets.all(20),
              child: [
                const _HolidaySegarCalc(),
                const _GlasgowCalc(),
                const _APGARCalc(),
                const _PedDosesCalc(),
                const _SilvermanCalc(),
                const _ShockIndexCalc(),
              ][_selectedCalc],
            ),
          ),
        ],
      ),
    );
  }
}

// ── Holiday-Segar ──────────────────────────────────────────────
class _HolidaySegarCalc extends StatefulWidget {
  const _HolidaySegarCalc();
  @override
  State<_HolidaySegarCalc> createState() => _HolidaySegarCalcState();
}
class _HolidaySegarCalcState extends State<_HolidaySegarCalc> {
  final _weightCtrl = TextEditingController();
  double? _result;

  void _calc() {
    final w = double.tryParse(_weightCtrl.text) ?? 0;
    double ml;
    if (w <= 10)      ml = w * 100;
    else if (w <= 20) ml = 1000 + (w - 10) * 50;
    else              ml = 1500 + (w - 20) * 20;
    setState(() => _result = ml);
  }

  @override
  Widget build(BuildContext context) => _CalcWrapper(
    title: '💧 Holiday-Segar',
    subtitle: 'Requerimiento basal de líquidos pediátricos',
    child: Column(children: [
      TextField(
        controller: _weightCtrl,
        keyboardType: const TextInputType.numberWithOptions(decimal: true),
        decoration: const InputDecoration(labelText: 'Peso (kg)', suffixText: 'kg'),
        onChanged: (_) => _calc(),
      ),
      if (_result != null) ...[
        const SizedBox(height: 20),
        _ResultBox(
          label: 'Requerimiento diario',
          value: '${_result!.toStringAsFixed(0)} mL/día',
          subvalue: '${(_result! / 24).toStringAsFixed(1)} mL/hora',
        ),
      ],
    ]),
  );
}

// ── Glasgow ────────────────────────────────────────────────────
class _GlasgowCalc extends StatefulWidget {
  const _GlasgowCalc();
  @override
  State<_GlasgowCalc> createState() => _GlasgowCalcState();
}
class _GlasgowCalcState extends State<_GlasgowCalc> {
  int _ojos = 4, _verbal = 5, _motor = 6;
  int get _total => _ojos + _verbal + _motor;
  String get _interp {
    if (_total <= 8)  return 'GRAVE — Considerar intubación';
    if (_total <= 12) return 'MODERADO — Observación estricta';
    return 'LEVE — Monitoreo';
  }
  Color get _color {
    if (_total <= 8)  return MedixColors.critical;
    if (_total <= 12) return MedixColors.warning;
    return MedixColors.success;
  }

  @override
  Widget build(BuildContext context) => _CalcWrapper(
    title: '🧠 Glasgow',
    subtitle: 'Escala de coma de Glasgow',
    child: Column(children: [
      _ScaleRow('Apertura ocular (E)', _ojos, 1, 4, (v) => setState(() => _ojos = v),
        ['1=Ninguna', '2=Dolor', '3=Verbal', '4=Espontánea']),
      const SizedBox(height: 16),
      _ScaleRow('Respuesta verbal (V)', _verbal, 1, 5, (v) => setState(() => _verbal = v),
        ['1=Ninguna', '2=Sonidos', '3=Palabras', '4=Confuso', '5=Orientado']),
      const SizedBox(height: 16),
      _ScaleRow('Respuesta motora (M)', _motor, 1, 6, (v) => setState(() => _motor = v),
        ['1=Ninguna', '2=Extensión', '3=Flexión', '4=Retirada', '5=Localiza', '6=Obedece']),
      const SizedBox(height: 20),
      Container(
        padding: const EdgeInsets.all(16),
        decoration: BoxDecoration(
          color: _color.withOpacity(0.1),
          borderRadius: BorderRadius.circular(12),
          border: Border.all(color: _color.withOpacity(0.4)),
        ),
        child: Row(mainAxisAlignment: MainAxisAlignment.spaceBetween, children: [
          Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
            const Text('GLASGOW TOTAL', style: TextStyle(color: MedixColors.textSecondary, fontSize: 12)),
            const SizedBox(height: 4),
            Text(_interp, style: TextStyle(color: _color, fontWeight: FontWeight.w600)),
          ]),
          Text('$_total/15', style: TextStyle(fontSize: 32, fontWeight: FontWeight.w700, color: _color)),
        ]),
      ),
    ]),
  );
}

// ── APGAR ──────────────────────────────────────────────────────
class _APGARCalc extends StatefulWidget {
  const _APGARCalc();
  @override
  State<_APGARCalc> createState() => _APGARCalcState();
}
class _APGARCalcState extends State<_APGARCalc> {
  int _fc = 2, _resp = 2, _tono = 2, _reflejos = 2, _color = 1;
  int get _total => _fc + _resp + _tono + _reflejos + _color;

  @override
  Widget build(BuildContext context) {
    String interp = _total >= 7 ? 'Normal (sin asfixia)' : _total >= 4 ? 'Depresión moderada' : 'Depresión severa';
    Color interpColor = _total >= 7 ? MedixColors.success : _total >= 4 ? MedixColors.warning : MedixColors.danger;

    return _CalcWrapper(
      title: '👶 APGAR',
      subtitle: 'Evaluación del recién nacido (1er y 5to minuto)',
      child: Column(children: [
        _ApgarRow('FC', _fc, (v) => setState(() => _fc = v), ['0=Sin FC', '1=<100', '2=≥100']),
        _ApgarRow('Respiración', _resp, (v) => setState(() => _resp = v), ['0=Ausente', '1=Irregular', '2=Llanto fuerte']),
        _ApgarRow('Tono muscular', _tono, (v) => setState(() => _tono = v), ['0=Flácido', '1=Alguna flex.', '2=Movimiento activo']),
        _ApgarRow('Reflejos', _reflejos, (v) => setState(() => _reflejos = v), ['0=Sin resp.', '1=Mueca', '2=Estornudo/tos']),
        _ApgarRow('Color', _color, (v) => setState(() => _color = v), ['0=Azul/pálido', '1=Extremidades azules', '2=Rosado']),
        const SizedBox(height: 16),
        _ResultBox(label: 'Score APGAR', value: '$_total/10', subvalue: interp, color: interpColor),
      ]),
    );
  }
}

// ── Dosis Pediátricas ──────────────────────────────────────────
class _PedDosesCalc extends StatefulWidget {
  const _PedDosesCalc();
  @override
  State<_PedDosesCalc> createState() => _PedDosesCalcState();
}
class _PedDosesCalcState extends State<_PedDosesCalc> {
  final _wCtrl = TextEditingController();

  final _meds = [
    {'name': 'Acetaminofén',    'dose': 15.0, 'unit': 'mg/kg/dosis',  'max': 1000.0, 'freq': 'c/6-8h'},
    {'name': 'Ibuprofeno',      'dose': 10.0, 'unit': 'mg/kg/dosis',  'max': 400.0,  'freq': 'c/8h'},
    {'name': 'Amoxicilina',     'dose': 25.0, 'unit': 'mg/kg/día',    'max': 500.0,  'freq': 'c/8h'},
    {'name': 'Diazepam (IV)',   'dose': 0.2,  'unit': 'mg/kg/dosis',  'max': 10.0,   'freq': 'PRN'},
    {'name': 'Adrenalina',      'dose': 0.01, 'unit': 'mg/kg',        'max': 1.0,    'freq': 'PRN PCR'},
    {'name': 'Dexametasona',    'dose': 0.15, 'unit': 'mg/kg/dosis',  'max': 10.0,   'freq': 'c/6h'},
  ];

  @override
  Widget build(BuildContext context) {
    final w = double.tryParse(_wCtrl.text) ?? 0;

    return _CalcWrapper(
      title: '💊 Dosis Pediátricas',
      subtitle: 'Medicamentos urgentes por peso',
      child: Column(children: [
        TextField(
          controller: _wCtrl,
          keyboardType: const TextInputType.numberWithOptions(decimal: true),
          decoration: const InputDecoration(labelText: 'Peso del paciente (kg)', suffixText: 'kg'),
          onChanged: (_) => setState(() {}),
        ),
        if (w > 0) ...[
          const SizedBox(height: 16),
          ...(_meds.map((m) {
            final calc = (m['dose'] as double) * w;
            final max = m['max'] as double;
            final dosis = calc > max ? max : calc;
            return Container(
              margin: const EdgeInsets.only(bottom: 10),
              padding: const EdgeInsets.all(14),
              decoration: BoxDecoration(
                color: MedixColors.bgSurface,
                borderRadius: BorderRadius.circular(10),
                border: Border.all(color: MedixColors.border),
              ),
              child: Row(children: [
                Expanded(child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                  Text(m['name'] as String, style: const TextStyle(fontWeight: FontWeight.w600)),
                  Text('${m['dose']} ${m['unit']} — ${m['freq']}',
                    style: const TextStyle(color: MedixColors.textMuted, fontSize: 11)),
                ])),
                Column(crossAxisAlignment: CrossAxisAlignment.end, children: [
                  Text('${dosis.toStringAsFixed(1)} mg',
                    style: const TextStyle(color: MedixColors.blue, fontWeight: FontWeight.w700, fontSize: 16)),
                  if (calc > max)
                    const Text('(máx)', style: TextStyle(color: MedixColors.warning, fontSize: 10)),
                ]),
              ]),
            );
          })),
        ],
      ]),
    );
  }
}

// ── Silverman ──────────────────────────────────────────────────
class _SilvermanCalc extends StatelessWidget {
  const _SilvermanCalc();
  @override
  Widget build(BuildContext context) => _CalcWrapper(
    title: '🫁 Silverman-Andersen',
    subtitle: 'Dificultad respiratoria neonatal',
    child: const Text('Calculadora en desarrollo. Escala: 0-10\n0=Sin DR | 1-3=Leve | 4-6=Moderada | 7-10=Severa',
      style: TextStyle(color: MedixColors.textSecondary)),
  );
}

// ── Shock Index ────────────────────────────────────────────────
class _ShockIndexCalc extends StatefulWidget {
  const _ShockIndexCalc();
  @override
  State<_ShockIndexCalc> createState() => _ShockIndexCalcState();
}
class _ShockIndexCalcState extends State<_ShockIndexCalc> {
  final _hrCtrl = TextEditingController();
  final _sbpCtrl = TextEditingController();

  @override
  Widget build(BuildContext context) {
    final hr = double.tryParse(_hrCtrl.text) ?? 0;
    final sbp = double.tryParse(_sbpCtrl.text) ?? 1;
    final si = sbp > 0 ? hr / sbp : 0.0;
    String interp = si < 0.6 ? 'Normal' : si < 1.0 ? 'Riesgo leve' : si < 1.4 ? 'Shock moderado' : 'Shock severo — Actuar AHORA';
    Color color = si < 0.6 ? MedixColors.success : si < 1.0 ? MedixColors.warning : MedixColors.danger;

    return _CalcWrapper(
      title: '❤️ Shock Index',
      subtitle: 'FC / PAS — Marcador de hipoperfusión',
      child: Column(children: [
        Row(children: [
          Expanded(child: TextField(
            controller: _hrCtrl,
            keyboardType: TextInputType.number,
            decoration: const InputDecoration(labelText: 'FC (lpm)'),
            onChanged: (_) => setState(() {}),
          )),
          const SizedBox(width: 12),
          Expanded(child: TextField(
            controller: _sbpCtrl,
            keyboardType: TextInputType.number,
            decoration: const InputDecoration(labelText: 'PAS (mmHg)'),
            onChanged: (_) => setState(() {}),
          )),
        ]),
        if (hr > 0 && sbp > 0) ...[
          const SizedBox(height: 16),
          _ResultBox(label: 'Shock Index', value: si.toStringAsFixed(2), subvalue: interp, color: color),
        ],
      ]),
    );
  }
}

// ── Helpers ────────────────────────────────────────────────────
class _CalcWrapper extends StatelessWidget {
  final String title, subtitle;
  final Widget child;
  const _CalcWrapper({required this.title, required this.subtitle, required this.child});

  @override
  Widget build(BuildContext context) => Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
    Text(title, style: const TextStyle(fontSize: 18, fontWeight: FontWeight.w700)),
    const SizedBox(height: 4),
    Text(subtitle, style: const TextStyle(color: MedixColors.textSecondary, fontSize: 13)),
    const SizedBox(height: 20),
    child,
  ]);
}

class _ResultBox extends StatelessWidget {
  final String label, value;
  final String? subvalue;
  final Color? color;
  const _ResultBox({required this.label, required this.value, this.subvalue, this.color});

  @override
  Widget build(BuildContext context) => Container(
    width: double.infinity,
    padding: const EdgeInsets.all(16),
    decoration: BoxDecoration(
      color: (color ?? MedixColors.blue).withOpacity(0.1),
      borderRadius: BorderRadius.circular(12),
      border: Border.all(color: (color ?? MedixColors.blue).withOpacity(0.3)),
    ),
    child: Column(children: [
      Text(label, style: const TextStyle(color: MedixColors.textSecondary, fontSize: 12)),
      const SizedBox(height: 6),
      Text(value, style: TextStyle(fontSize: 28, fontWeight: FontWeight.w700, color: color ?? MedixColors.blue)),
      if (subvalue != null) ...[
        const SizedBox(height: 4),
        Text(subvalue!, style: TextStyle(color: color ?? MedixColors.blue, fontWeight: FontWeight.w600)),
      ],
    ]),
  );
}

class _ScaleRow extends StatelessWidget {
  final String label;
  final int value, min, max;
  final ValueChanged<int> onChanged;
  final List<String> hints;
  const _ScaleRow(this.label, this.value, this.min, this.max, this.onChanged, this.hints);

  @override
  Widget build(BuildContext context) => Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
    Text(label, style: const TextStyle(fontWeight: FontWeight.w500)),
    Row(children: [
      Expanded(child: Slider(
        value: value.toDouble(), min: min.toDouble(), max: max.toDouble(), divisions: max - min,
        activeColor: MedixColors.blue,
        onChanged: (v) => onChanged(v.round()),
      )),
      Container(
        width: 32, height: 32,
        decoration: BoxDecoration(color: MedixColors.blue, borderRadius: BorderRadius.circular(8)),
        alignment: Alignment.center,
        child: Text('$value', style: const TextStyle(color: Colors.white, fontWeight: FontWeight.w700)),
      ),
    ]),
    Text(hints[value - min], style: const TextStyle(color: MedixColors.textMuted, fontSize: 11)),
  ]);
}

class _ApgarRow extends StatelessWidget {
  final String label;
  final int value;
  final ValueChanged<int> onChanged;
  final List<String> hints;
  const _ApgarRow(this.label, this.value, this.onChanged, this.hints);

  @override
  Widget build(BuildContext context) => Padding(
    padding: const EdgeInsets.only(bottom: 12),
    child: Row(children: [
      Expanded(child: Text(label)),
      ...List.generate(3, (i) => GestureDetector(
        onTap: () => onChanged(i),
        child: Container(
          margin: const EdgeInsets.only(left: 6),
          width: 36, height: 36,
          decoration: BoxDecoration(
            color: value == i ? MedixColors.blue : MedixColors.bgSurface,
            borderRadius: BorderRadius.circular(8),
            border: Border.all(color: value == i ? MedixColors.blue : MedixColors.border),
          ),
          alignment: Alignment.center,
          child: Text('$i', style: TextStyle(
            color: value == i ? Colors.white : MedixColors.textSecondary,
            fontWeight: FontWeight.w600,
          )),
        ),
      )),
    ]),
  );
}
