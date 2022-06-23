// RUN: circt-opt -lower-firrtl-to-hw=add-pragmas-to-multibit-mux -verify-diagnostics %s | FileCheck %s

firrtl.circuit "MultibitMux" {
  firrtl.module @MultibitMux(in %a_0: !firrtl.uint<1>, in %a_1: !firrtl.uint<1>, in %a_2: !firrtl.uint<1>, in %sel: !firrtl.uint<2>, out %b: !firrtl.uint<1>) {
    %0 = firrtl.multibit_mux %sel, %a_2, %a_1, %a_0 : !firrtl.uint<2>, !firrtl.uint<1>
    firrtl.strictconnect %b, %0 : !firrtl.uint<1>
    // CHECK:      %0 = hw.array_create %a_2, %a_1, %a_0 : i1
    // CHECK-NEXT: %1 = sv.wire sym @[[ARRAY:.+]]  : !hw.inout<array<3xi1>>
    // CHECK-NEXT: sv.assign %1, %0 : !hw.array<3xi1>
    // CHECK-NEXT: %2 = sv.wire sym @[[VAL:.+]]  : !hw.inout<i1>
    // CHECK-NEXT{LITERAL}: sv.verbatim "assign {{2}} = {{1}}[{{0}}] /* cadence map_to_mux */; /* synopsys infer_mux_override */"(%sel) : i2
    // CHECK-SAME: {symbols = [#hw.innerNameRef<@MultibitMux::@[[ARRAY]]>, #hw.innerNameRef<@MultibitMux::@[[VAL]]>]}
    // CHECK-NEXT: %3 = sv.read_inout %2 : !hw.inout<i1>
  }
}