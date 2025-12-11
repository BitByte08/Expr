<script setup lang="ts">
import { computed } from 'vue';

const props = defineProps<{ isUser: boolean; text: string; isHtml?: boolean }>();

// 간단한 마크다운 -> HTML 변환
function parseMarkdown(md: string): string {
  if (!md) return '';
  
  let html = md;
  
  // 코드 블록 (```code``` -> <pre><code>code</code></pre>) - 먼저 처리
  html = html.replace(/```(.*?)```/gs, '<pre><code>$1</code></pre>');
  
  // 테이블 처리
  const lines = html.split('\n');
  let inTable = false;
  let tableLines: string[] = [];
  const processedLines: string[] = [];
  
  for (let i = 0; i < lines.length; i++) {
    const line = lines[i] || '';
    const isTableLine = line.trim().startsWith('|') && line.trim().endsWith('|');
    
    if (isTableLine) {
      if (!inTable) {
        inTable = true;
        tableLines = [];
      }
      tableLines.push(line.trim());
    } else {
      if (inTable && tableLines.length >= 2) {
        // 테이블 변환
        const headerLine = tableLines[0] || '';
        const sepLine = tableLines[1] || '';
        
        if (/^\|[\s\-:|]+\|$/.test(sepLine)) {
          const headers = headerLine.split('|').filter((h: string) => h.trim()).map((h: string) => h.trim());
          let table = '<table border="1" style="border-collapse: collapse; border: 2px solid white;"><thead><tr>';
          headers.forEach((h: string) => table += `<th style="border: 1px solid white; padding: 10px;">${h}</th>`);
          table += '</tr></thead><tbody>';
          
          for (let j = 2; j < tableLines.length; j++) {
            const row = tableLines[j] || '';
            const cells = row.split('|').filter((c: string) => c.trim()).map((c: string) => c.trim());
            table += '<tr>';
            cells.forEach((c: string) => table += `<td style="border: 1px solid white; padding: 10px;">${c}</td>`);
            table += '</tr>';
          }
          table += '</tbody></table>';
          processedLines.push(table);
        } else {
          processedLines.push(...tableLines);
        }
      } else if (inTable) {
        processedLines.push(...tableLines);
      }
      inTable = false;
      tableLines = [];
      processedLines.push(line);
    }
  }
  
  if (inTable && tableLines.length >= 2) {
    const headerLine = tableLines[0] || '';
    const sepLine = tableLines[1] || '';
    
    if (/^\|[\s\-:|]+\|$/.test(sepLine)) {
      const headers = headerLine.split('|').filter((h: string) => h.trim()).map((h: string) => h.trim());
      let table = '<table border="1" style="border-collapse: collapse; border: 2px solid white;"><thead><tr>';
      headers.forEach((h: string) => table += `<th style="border: 1px solid white; padding: 10px;">${h}</th>`);
      table += '</tr></thead><tbody>';
      
      for (let j = 2; j < tableLines.length; j++) {
        const row = tableLines[j] || '';
        const cells = row.split('|').filter((c: string) => c.trim()).map((c: string) => c.trim());
        table += '<tr>';
        cells.forEach((c: string) => table += `<td style="border: 1px solid white; padding: 10px;">${c}</td>`);
        table += '</tr>';
      }
      table += '</tbody></table>';
      processedLines.push(table);
    }
  }
  
  html = processedLines.join('\n');
  
  // 인라인 코드 (`code` -> <code>code</code>)
  html = html.replace(/`(.*?)`/g, '<code>$1</code>');
  
  // 수평선 (--- 또는 ***)
  html = html.replace(/^[\-*]{3,}$/gm, '<hr>');
  
  // 헤딩 (### -> <h3>, ## -> <h2>, # -> <h1>)
  html = html.replace(/^### (.*?)$/gm, '<h3>$1</h3>');
  html = html.replace(/^## (.*?)$/gm, '<h2>$1</h2>');
  html = html.replace(/^# (.*?)$/gm, '<h1>$1</h1>');
  
  // 볼드 (**text** -> <strong>text</strong>)
  html = html.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
  
  // 이탤릭 (*text* -> <em>text</em>)
  html = html.replace(/\*(.*?)\*/g, '<em>$1</em>');
  
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
}

.bubble h1, .bubble h2, .bubble h3 {
  margin: 12px 0 8px 0;
  font-weight: 600;
  line-height: 1.3;
}

.bubble h1 {
  font-size: 1.5em;
}

.bubble h2 {
  font-size: 1.3em;
}

.bubble h3 {
  font-size: 1.1em;
}

.bubble table,
.bubble .md-table {
  width: 100%;
  border-collapse: collapse;
  margin: 12px 0;
  background: rgba(0, 0, 0, 0.3);
  border: 2px solid #ffffff;
}

.bubble table th,
.bubble table td,
.bubble .md-table th,
.bubble .md-table td {
  padding: 10px 14px;
  text-align: left;
  border: 1px solid #ffffff;
}

.bubble table th,
.bubble .md-table th {
  background: rgba(255, 255, 255, 0.2);
  font-weight: 600;
}

.bubble table tbody tr:hover {
  background: rgba(255, 255, 255, 0.08);
}

.bubble hr {
  border: none;
  border-top: 1px solid rgba(255, 255, 255, 0.08);
  margin: 16px 0;
}

.row.user .bubble {
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