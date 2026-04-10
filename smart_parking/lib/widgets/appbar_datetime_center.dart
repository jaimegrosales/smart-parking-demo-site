import 'package:flutter/material.dart';

class AppBarDateTimeCenter extends StatelessWidget {
  const AppBarDateTimeCenter({super.key});

  @override
  Widget build(BuildContext context) {
    final screenWidth = MediaQuery.of(context).size.width;
    final bool useCompact = screenWidth < 760;
    final double fontSize = screenWidth < 430 ? 11 : (useCompact ? 13 : 15);
    final bool anchorRight = screenWidth < 760;

    return IgnorePointer(
      child: SafeArea(
        child: Align(
          alignment: anchorRight ? Alignment.centerRight : Alignment.center,
          child: Padding(
            padding: EdgeInsets.only(right: anchorRight ? 56 : 0),
            child: StreamBuilder<DateTime>(
            stream: Stream<DateTime>.periodic(
              const Duration(seconds: 1),
              (_) => DateTime.now(),
            ),
            initialData: DateTime.now(),
            builder: (context, snapshot) {
              final now = snapshot.data ?? DateTime.now();
              const weekdays = [
                'Mon',
                'Tue',
                'Wed',
                'Thu',
                'Fri',
                'Sat',
                'Sun',
              ];
              const months = [
                'Jan',
                'Feb',
                'Mar',
                'Apr',
                'May',
                'Jun',
                'Jul',
                'Aug',
                'Sep',
                'Oct',
                'Nov',
                'Dec',
              ];
              final hour12 = now.hour == 0 || now.hour == 12 ? 12 : now.hour % 12;
              final amPm = now.hour < 12 ? 'AM' : 'PM';
              final fullLabel =
                  '${weekdays[now.weekday - 1]}, ${months[now.month - 1]} ${now.day}  |  $hour12:${now.minute.toString().padLeft(2, '0')} $amPm';
              final compactLabel =
                  '${weekdays[now.weekday - 1]}, ${months[now.month - 1]} ${now.day}';

              return Text(
                useCompact ? compactLabel : fullLabel,
                style: TextStyle(
                  color: const Color.fromRGBO(235, 235, 240, 1),
                  fontSize: fontSize,
                  fontWeight: FontWeight.w500,
                ),
                textAlign: anchorRight ? TextAlign.right : TextAlign.center,
                maxLines: 1,
                overflow: TextOverflow.ellipsis,
              );
            },
          ),
          ),
        ),
      ),
    );
  }
}
