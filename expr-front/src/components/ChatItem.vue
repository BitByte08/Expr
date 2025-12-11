<script setup lang="ts">
import { computed } from 'vue';

const props = defineProps<{ isUser: boolean; text: string; isHtml?: boolean }>();

// 간단한 마크다운 -> HTML 변환
function parseMarkdown(md: string): string {
  if (!md) return '';
  
  // 볼드 (**text** -> <strong>text</strong>)
  let html = md.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
  
  // 이탤릭 (*text* -> <em>text</em>)
  html = html.replace(/\*(.*?)\*/g, '<em>$1</em>');
  
  // 코드 블록 (```code``` -> <pre><code>code</code></pre>)
  html = html.replace(/```(.*?)```/gs, '<pre><code>$1</code></pre>');
  
  // 인라인 코드 (`code` -> <code>code</code>)
  html = html.replace(/`(.*?)`/g, '<code>$1</code>');
  
  // 줄바꿈 (\n -> <br>)
  html = html.replace(/\n/g, '<br>');
  
  return html;
}

const displayText = computed(() => props.isHtml ? parseMarkdown(props.text) : props.text);
</script>

<template>
  <div class="row" :class="{ user: props.isUser }">
    <div v-if="props.isHtml" class="bubble" v-html="displayText"></div>
    <div v-else class="bubble">{{ displayText }}</div>
  </div>
</template><style scoped>
.row {
    display: flex;
    justify-content: flex-start;
    padding: 6px 0;
}

.row.user {
    justify-content: flex-end;
}

.bubble {
  max-width: min(680px, 78vw);
  padding: 12px 14px;
  border-radius: 18px;
  line-height: 1.55;
  background: rgba(255, 255, 255, 0.08);
  color: #f9fbff;
  border: 1px solid rgba(255, 255, 255, 0.12);
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.18);
  backdrop-filter: blur(10px);
  transition: transform 120ms ease, border-color 120ms ease;
  word-break: break-word;
  white-space: normal;
}

.bubble code {
  background: rgba(0, 0, 0, 0.3);
  padding: 2px 6px;
  border-radius: 4px;
  font-family: monospace;
  font-size: 0.9em;
}

.bubble pre {
  background: rgba(0, 0, 0, 0.3);
  padding: 10px;
  border-radius: 6px;
  overflow-x: auto;
  margin: 8px 0;
}

.bubble pre code {
  background: transparent;
  padding: 0;
}.row.user .bubble {
    background: linear-gradient(135deg, #4b8dff, #6cc7ff);
    color: #0a1a2f;
    border: 1px solid rgba(0, 0, 0, 0.05);
    border-radius: 18px;
}

.bubble:hover {
    transform: translateY(-2px);
    border-color: rgba(255, 255, 255, 0.2);
}
</style>