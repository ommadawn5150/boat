#include "userosc.h"

void OSC_INIT(uint32_t platform, uint32_t api) {
  // 初期化処理
}

void OSC_CYCLE(const user_osc_param_t * const params,
               int32_t *yn,
               const uint32_t frames) {
  // サンプル生成処理（Q31 固定小数点）
  for (uint32_t i = 0; i < frames; i++) {
    yn[i] = 0; // 無音（ここに波形生成を実装する）
  }
}

void OSC_NOTEON(const user_osc_param_t * const params) {
  // ノートオン処理
}

void OSC_NOTEOFF(const user_osc_param_t * const params) {
  // ノートオフ処理
}

void OSC_PARAM(uint16_t index, uint16_t value) {
  // パラメータ変更処理（index: 0-5, value: 0-100 または 0-200 bipolar）
}
