
<script setup lang="ts">
import { ref, computed, onMounted } from "vue";
import { useRouter } from "vue-router";

type ChatMessage = { sender: "user" | "ai"; text: string };
type ChatSession = { id: string; title: string; messages: ChatMessage[] };

const STORAGE_KEY = "chat_sessions_v1";
const router = useRouter();

const userInput = ref("");
const sessions = ref<ChatSession[]>([]);

const recentSessions = computed(() => sessions.value.slice(-3).reverse());

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
});

const startNewChat = () => {
    const trimmed = userInput.value.trim();
    router.push(trimmed ? { path: "/chat", query: { q: trimmed } } : { path: "/chat" });
    if (trimmed) {
        userInput.value = "";
    }
};

const loadSession = (session: ChatSession) => {
    router.push(`/chat/${session.id}`);
};
</script>

<template>
    <div class="page">
        <div class="hero">
            <div class="composer shell" @keyup.enter="startNewChat">
                <input
                    v-model="userInput"
                    placeholder="무엇을 찾고 싶나요?"
                    @keyup.enter="startNewChat"
                />
                <button type="button" @click="startNewChat">
                    ➤
                </button>
            </div>

            <div v-if="recentSessions.length" class="dock">
                <div
                    v-for="item in recentSessions"
                    :key="item.id"
                    class="dock-item"
                    @click="loadSession(item)"
                >
                    {{ item.title || '세션' }}
                </div>
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

.hero {
    width: min(720px, 100%);
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 18px;
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
    box-shadow: 0 16px 50px rgba(0, 0, 0, 0.28);
    padding: 12px 12px 12px 18px;
    width: 100%;
}

.composer input {
    width: 100%;
    padding: 10px 2px;
    border-radius: 16px;
    border: none;
    background: transparent;
    color: #e8f0ff;
}

.composer input::placeholder {
    color: rgba(232, 240, 255, 0.5);
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

.dock {
    display: flex;
    gap: 12px;
    padding: 10px 12px;
    background: rgba(255, 255, 255, 0.04);
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 18px;
    box-shadow: 0 16px 40px rgba(0, 0, 0, 0.28);
    width: 100%;
}

.dock-item {
    min-width: 120px;
    padding: 10px 12px;
    border-radius: 12px;
    background: rgba(255, 255, 255, 0.06);
    border: 1px solid rgba(255, 255, 255, 0.08);
    text-align: center;
    cursor: pointer;
    transition: transform 180ms ease, box-shadow 180ms ease;
}

.dock-item:hover {
    transform: translateY(-6px) scale(1.03);
    box-shadow: 0 14px 28px rgba(0, 0, 0, 0.28);
}

@media (max-width: 720px) {
    .page {
        padding: 16px;
    }

    .hero {
        gap: 12px;
    }
}
</style>
