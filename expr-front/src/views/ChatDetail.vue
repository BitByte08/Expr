<script setup lang="ts">
import ChatItem from "../components/ChatItem.vue";
import { ref, nextTick, computed, onMounted, watch } from "vue";
import { useRouter, useRoute } from "vue-router";

type ChatMessage = { sender: "user" | "ai"; text: string };
type ChatSession = { id: string; title: string; messages: ChatMessage[] };
const MAX_HISTORY_ITEMS = 10;
const MAX_HISTORY_TEXT_LENGTH = 1200;

const STORAGE_KEY = "chat_sessions_v1";
const router = useRouter();
const route = useRoute();

const userInput = ref("");
const messages = ref<ChatMessage[]>([]);
const isLoading = ref(false);
const messageRef = ref<HTMLElement | null>(null);
const currentAiMessage = ref<ChatMessage | null>(null);
const sessions = ref<ChatSession[]>([]);
const currentSessionId = ref<string | null>(null);

onMounted(() => {
    try {
        const saved = localStorage.getItem(STORAGE_KEY);
        if (saved) {
            const parsed = JSON.parse(saved) as ChatSession[];
            if (Array.isArray(parsed)) {
                sessions.value = parsed;
            }
        }
    } catch (e) {
        console.warn("세션 로드 실패", e);
    }

    // URL에서 세션 ID를 가져와서 로드
    const sessionId = route.params.id as string;
    if (sessionId) {
        const session = sessions.value.find((s) => s.id === sessionId);
        if (session) {
            loadSession(session);
        }
    } else {
        // 새 세션
        currentSessionId.value = `${Date.now()}`;
        messages.value = [];
    }

        // 홈에서 검색어를 전달받은 경우 즉시 전송
        const initialPrompt = (route.query.q as string) || "";
        if (initialPrompt.trim()) {
            userInput.value = initialPrompt.trim();
            nextTick(() => sendMessage());
        }
});

watch(
    messages,
    (val) => {
        if (!currentSessionId.value) return;
        const updated: ChatSession = {
            id: currentSessionId.value,
            title: sessionTitle(val),
            messages: val,
        };
        const others = sessions.value.filter((s) => s.id !== updated.id);
        sessions.value = [...others, updated];
        try {
            localStorage.setItem(STORAGE_KEY, JSON.stringify(sessions.value));
        } catch (e) {
            console.warn("세션 저장 실패", e);
        }
    },
    { deep: true }
);

function sessionTitle(msgs: ChatMessage[]): string {
    const firstUser = msgs.find((m) => m.sender === "user");
    if (!firstUser) return "새 세션";
    return firstUser.text.slice(0, 30) || "새 세션";
}

const scrollToBottom = () => {
    nextTick(() => {
        if (messageRef.value) {
            messageRef.value.scrollTop = messageRef.value.scrollHeight;
        }
    });
};

const connectSSE = (prompt: string) => {
    currentAiMessage.value = { sender: "ai", text: "" };
    isLoading.value = true;
    if (currentAiMessage.value) {
        messages.value.push(currentAiMessage.value);
    }

    // 이전 메시지를 히스토리로 전송 (로딩 중인 AI 메시지 제외)
    const historyRaw = messages.value.slice(0, -1);
    const trimmedHistory = historyRaw
        .slice(-MAX_HISTORY_ITEMS)
        .map((m) => ({
            sender: m.sender,
            text: m.text.slice(-MAX_HISTORY_TEXT_LENGTH),
        }));
    const historyParam = encodeURIComponent(JSON.stringify(trimmedHistory));
    // Cloudflare Worker MCP 클라이언트로 직접 연결
    const eventSource = new EventSource(`https://mcp-worker.bitbyte08.workers.dev/api/chat?prompt=${encodeURIComponent(prompt)}&history=${historyParam}`);

    eventSource.addEventListener("status", (event) => {
        try {
            const data = JSON.parse(event.data);
            if (data.status === "STREAMING_END") {
                eventSource.close();
                isLoading.value = false;
            }
        } catch (error) {
            console.error("Error parsing status event data:", error);
        }
    });

    eventSource.addEventListener("chunk", (event) => {
        try {
            const data = JSON.parse(event.data);
            if (currentAiMessage.value && data?.text) {
                currentAiMessage.value.text += data.text;
                // 배열 참조를 갱신해 뷰 업데이트를 확실히 반영
                messages.value = [...messages.value];
                nextTick(() => scrollToBottom());
            }
        } catch (error) {
            console.error("Error parsing chunk event data:", error);
        }
    });

    // 혹시 기본 message 이벤트로 오는 SSE 대비
    eventSource.onmessage = (event) => {
        try {
            const data = JSON.parse(event.data);
            if (currentAiMessage.value && data?.text) {
                currentAiMessage.value.text += data.text;
                messages.value = [...messages.value];
                scrollToBottom();
            }
        } catch (error) {
            // 무시
        }
    };

    eventSource.onerror = (error) => {
        console.error("SSE Error:", error);
        eventSource.close();
        isLoading.value = false;
        if (currentAiMessage.value && currentAiMessage.value.text === "") {
            currentAiMessage.value.text = "⚠️ 서버와의 연결이 끊겼거나 오류가 발생했습니다.";
        }
    };
};

const sendMessage = () => {
    if (!userInput.value.trim() || isLoading.value) return;

    if (!currentSessionId.value) {
        currentSessionId.value = `${Date.now()}`;
    }

    messages.value.push({ sender: "user", text: userInput.value });
    const currentPrompt = userInput.value;
    userInput.value = "";

    scrollToBottom();
    connectSSE(currentPrompt);
};

const goBack = () => {
    router.push("/");
};

const loadSession = (session: ChatSession) => {
    currentSessionId.value = session.id;
    messages.value = JSON.parse(JSON.stringify(session.messages));
    userInput.value = "";
    scrollToBottom();
};
</script>

<template>
    <div class="page">
        <div class="chat-shell">
            <header class="chat-header">
                <button class="back-btn" @click="goBack">← 뒤로가기</button>
            </header>

            <div class="chat-window" ref="messageRef">
                <ChatItem
                    v-for="(msg, index) in messages.filter(m => m.text.trim())"
                    :key="index"
                    :isUser="msg.sender === 'user'"
                    :text="msg.text"
                    :isHtml="msg.sender === 'ai'"
                />
                <div v-if="isLoading && (!currentAiMessage || !currentAiMessage.text.trim())" class="thinking">
                    <span></span><span></span><span></span>
                </div>
            </div>

            <div class="composer shell" @keyup.enter="sendMessage">
                <input
                    v-model="userInput"
                    :disabled="isLoading"
                    placeholder="메시지를 입력하세요"
                />
                <button type="button" @click="sendMessage" :disabled="isLoading || !userInput.trim()">
                    ➤
                </button>
            </div>
        </div>
    </div>
</template>

<style scoped>
.page {
    min-height: 100vh;
    background: linear-gradient(180deg, #0b1221 0%, #0f172a 40%, #0b1020 100%);
    color: #e8f0ff;
    padding: 18px;
    display: flex;
    align-items: center;
    justify-content: center;
}

.chat-shell {
    width: min(1000px, 100%);
    display: flex;
    flex-direction: column;
    gap: 12px;
    min-height: 80vh;
    position: relative;
}

.chat-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 6px 4px 2px;
}

.title {
    font-weight: 700;
    letter-spacing: 0.06em;
    text-transform: uppercase;
    flex: 1;
    text-align: center;
}

.back-btn {
    padding: 8px 16px;
    border: 1px solid rgba(255, 255, 255, 0.12);
    border-radius: 8px;
    background: rgba(255, 255, 255, 0.04);
    color: #e8f0ff;
    cursor: pointer;
    font-size: 14px;
    transition: background 120ms ease, border-color 120ms ease;
    font-weight: 500;
}

.back-btn:hover {
    background: rgba(255, 255, 255, 0.08);
    border-color: rgba(255, 255, 255, 0.2);
}

.chat-window {
    flex: 1;
    overflow-y: auto;
    padding: 14px 10px;
    border-radius: 28px;
    border: none;
    background: transparent;
}

.chat-window::-webkit-scrollbar {
    width: 6px;
}

.chat-window::-webkit-scrollbar-track {
    background: transparent;
}

.chat-window::-webkit-scrollbar-thumb {
    background: rgba(255, 255, 255, 0.1);
    border-radius: 3px;
}

.composer {
    display: grid;
    grid-template-columns: 1fr auto;
    gap: 10px;
    padding: 10px;
    background: transparent;
}

.composer.shell {
    background: rgba(255, 255, 255, 0.04);
    border: 1px solid rgba(255, 255, 255, 0.12);
    border-radius: 999px;
    box-shadow: 0 16px 50px rgba(0, 0, 0, 0.28), 0 -20px 40px rgba(11, 18, 33, 0.6);
    padding: 12px 12px 12px 18px;
    position: sticky;
    bottom: 15px;
    z-index: 10;
    backdrop-filter: blur(8px);
}

.composer input {
    width: 100%;
    padding: 10px 2px;
    border-radius: 16px;
    border: none;
    background: transparent;
    color: #e8f0ff;
}

.composer input:focus {
    outline: none;
}

.composer button {
    width: 46px;
    height: 46px;
    border: none;
    border-radius: 999px;
    background: #1a73e8;
    color: #f2f6ff;
    font-size: 18px;
    font-weight: 700;
    cursor: pointer;
    transition: transform 140ms ease, box-shadow 140ms ease, opacity 120ms ease;
    display: inline-flex;
    align-items: center;
    justify-content: center;
}

.composer button:disabled {
    opacity: 0.6;
    cursor: not-allowed;
}

.composer button:not(:disabled):hover {
    box-shadow: 0 12px 28px rgba(26, 115, 232, 0.35);
    transform: translateY(-1px);
}

.thinking {
    display: inline-flex;
    gap: 8px;
    padding: 12px 14px;
    margin-top: 6px;
    border-radius: 14px;
    background: rgba(255, 255, 255, 0.04);
    border: 1px solid rgba(255, 255, 255, 0.08);
    width: fit-content;
}

.thinking span {
    width: 8px;
    height: 8px;
    border-radius: 999px;
    background: #7ad7ff;
    animation: bounce 1.2s infinite ease-in-out;
}

.thinking span:nth-child(2) {
    animation-delay: 0.2s;
}

.thinking span:nth-child(3) {
    animation-delay: 0.4s;
}

@keyframes bounce {
    0%, 80%, 100% {
        transform: scale(0.6);
        opacity: 0.6;
    }
    40% {
        transform: scale(1);
        opacity: 1;
    }
}

@media (max-width: 720px) {
    .page {
        padding: 16px;
    }

    .chat-shell {
        min-height: 82vh;
    }

    .back-btn {
        padding: 6px 12px;
        font-size: 12px;
    }
}
</style>
