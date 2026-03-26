#include "userdelfx.h"

void DELFX_INIT(uint32_t platform, uint32_t api) {
  // 初期化処理
}

void DELFX_PROCESS(float *xn, uint32_t frames) {
  // インターリーブステレオ処理（xn: L,R,L,R,...）
  // wet/dry ミックスもここで行う
}

void DELFX_SUSPEND(void) {
  // エフェクト停止時の処理
}

void DELFX_RESUME(void) {
  // エフェクト再開時の処理
}

void DELFX_PARAM(uint8_t index, int32_t value) {
  // パラメータ変更処理（value: 0-1023、10-bit 解像度）
  // index 0: time, 1: depth, 2: shift-depth
}
