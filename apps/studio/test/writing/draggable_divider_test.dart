import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:docs_agent/widgets/draggable_divider.dart';

void main() {
  group('DraggableDivider', () {
    testWidgets('renders divider bar', (tester) async {
      await tester.pumpWidget(MaterialApp(
        home: Scaffold(
          body: Row(
            children: [
              const Expanded(child: SizedBox()),
              DraggableDivider(
                isLeft: true,
                onDrag: (_) {},
              ),
              const Expanded(child: SizedBox()),
            ],
          ),
        ),
      ));
      expect(find.byType(DraggableDivider), findsOneWidget);
    });

    testWidgets('calls onDrag on pan', (tester) async {
      double dragDelta = 0;
      await tester.pumpWidget(MaterialApp(
        home: Scaffold(
          body: Row(
            children: [
              const Expanded(child: SizedBox()),
              DraggableDivider(
                isLeft: true,
                onDrag: (delta) => dragDelta = delta,
              ),
              const Expanded(child: SizedBox()),
            ],
          ),
        ),
      ));
      final divider = find.byType(DraggableDivider);
      await tester.drag(divider, const Offset(10, 0));
      expect(dragDelta, 10);
    });
  });
}
