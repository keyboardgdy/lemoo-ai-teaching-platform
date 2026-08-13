<script setup lang="ts">
import { Bot, CheckCircle2, Construction, ShieldAlert } from '@lucide/vue'
import { useI18n } from 'vue-i18n'

const { t } = useI18n()
</script>

<template>
  <main id="main-content" class="page-shell" tabindex="-1">
    <section class="status-card" aria-labelledby="page-title">
      <div class="brand-mark" aria-hidden="true">
        <Bot :size="28" :stroke-width="1.8" />
      </div>
      <p class="eyebrow">Simulator-only</p>
      <h1 id="page-title">{{ t('title') }}</h1>
      <p class="stage">{{ t('stage') }}</p>
      <p class="description">{{ t('description') }}</p>

      <ul class="status-list" aria-label="工程状态">
        <li>
          <CheckCircle2 aria-hidden="true" />
          <span>{{ t('gate0') }}</span>
        </li>
        <li>
          <Construction aria-hidden="true" />
          <span>{{ t('w2') }}</span>
        </li>
        <li class="blocked">
          <ShieldAlert aria-hidden="true" />
          <span>{{ t('blocked') }}</span>
        </li>
      </ul>
    </section>
  </main>
</template>
