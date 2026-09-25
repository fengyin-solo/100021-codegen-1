<template>
  <section class="page cockpit" data-module="cockpit">
    <header class="page-head">
      <div>
        <h2>剧本审稿驾驶舱</h2>
        <p class="page-desc">按推进阶段纵览每部剧本的题材、集数、版本与定稿日期；点开可查审稿记录、版权归属与阶段变更时间。</p>
      </div>
      <div class="page-actions">
        <div class="mode-switch" role="tablist" aria-label="视图切换">
          <button
            type="button"
            role="tab"
            :class="['mode-btn', { active: mode === 'list' }]"
            :aria-selected="mode === 'list'"
            @click="mode = 'list'"
          >
            列表
          </button>
          <button
            type="button"
            role="tab"
            :class="['mode-btn', { active: mode === 'board' }]"
            :aria-selected="mode === 'board'"
            @click="mode = 'board'"
          >
            看板
          </button>
        </div>
      </div>
    </header>

    <div class="stat-row">
      <article v-for="item in stageCounts" :key="item.stage" class="stat-card">
        <span class="stat-label">{{ item.stage }}</span>
        <strong class="stat-value">{{ item.count }}</strong>
      </article>
    </div>

    <form class="filter-bar" @submit.prevent="reload">
      <label class="filter-item">
        <span>推进阶段</span>
        <select v-model="stageFilter">
          <option value="">全部阶段</option>
          <option v-for="stage in stages" :key="stage" :value="stage">{{ stage }}</option>
        </select>
      </label>
      <label class="filter-item">
        <span>剧本检索</span>
        <input v-model="keyword" placeholder="按剧本编号或名称检索" />
      </label>
      <button class="btn" type="submit">查询</button>
      <button class="btn ghost" type="button" @click="resetFilters">重置条件</button>
    </form>

    <div v-if="loading" class="state-box">剧本数据加载中…</div>
    <div v-else-if="loadError" class="state-box error-box">
      <p class="error-text">{{ loadError }}</p>
      <button class="btn primary" type="button" @click="reload">重试</button>
    </div>

    <template v-else>
      <table v-if="mode === 'list'" class="data-table">
        <thead>
          <tr>
            <th>推进阶段</th>
            <th v-for="column in columns" :key="column">{{ column }}</th>
            <th>审稿记录</th>
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="item in items"
            :key="item.id"
            :class="{ selected: selectedId === item.id }"
            class="clickable-row"
            @click="openDetail(item.id)"
          >
            <td><span :class="['stage-tag', stageClass(item.推进阶段)]">{{ item.推进阶段 ?? '—' }}</span></td>
            <td v-for="column in columns" :key="column">{{ item[column] || '—' }}</td>
            <td>{{ item.审稿记录数 }} 条<span v-if="item.最新审稿状态"> · {{ item.最新审稿状态 }}</span></td>
          </tr>
          <tr v-if="!items.length">
            <td :colspan="columns.length + 2" class="empty-state">当前条件下没有剧本，换个阶段或关键词试试</td>
          </tr>
        </tbody>
      </table>

      <div v-else class="kanban">
        <div v-for="stage in boardColumns" :key="stage.name" class="kanban-col">
          <header class="kanban-head">
            <span :class="['stage-tag', stageClass(stage.name)]">{{ stage.name }}</span>
            <span class="kanban-count">{{ stage.items.length }}</span>
          </header>
          <!-- 看板卡片与列表行同一份 items、同一组 columns，口径一致 -->
          <button
            v-for="item in stage.items"
            :key="item.id"
            type="button"
            :class="['kanban-card', { selected: selectedId === item.id }]"
            @click="openDetail(item.id)"
          >
            <strong class="kanban-title">{{ item.剧本名称 || '未命名剧本' }}</strong>
            <span class="kanban-code">{{ item.剧本编号 }}</span>
            <dl class="kanban-meta">
              <template v-for="column in columns" :key="column">
                <dt>{{ column }}</dt>
                <dd>{{ item[column] || '—' }}</dd>
              </template>
              <dt>审稿记录</dt>
              <dd>{{ item.审稿记录数 }} 条<span v-if="item.最新审稿状态"> · {{ item.最新审稿状态 }}</span></dd>
            </dl>
          </button>
          <p v-if="!stage.items.length" class="kanban-empty">该阶段暂无剧本</p>
        </div>
      </div>

      <p v-if="!items.length" class="page-foot-hint">列表与看板在当前筛选下均无数据</p>
    </template>

    <!-- 详情抽屉：审稿记录、版权归属、阶段变更时间 -->
    <div v-if="detailOpen" class="drawer-mask" @click.self="closeDetail">
      <aside class="drawer" :aria-busy="detailLoading">
        <header class="drawer-head">
          <div>
            <h3>{{ detail?.剧本名称 || '剧本详情' }}</h3>
            <p class="page-desc">{{ detail?.剧本编号 }} · <span :class="['stage-tag', stageClass(detail?.推进阶段)]">{{ detail?.推进阶段 }}</span></p>
          </div>
          <button class="btn ghost" type="button" @click="closeDetail">关闭</button>
        </header>

        <div v-if="detailLoading" class="state-box">审稿信息加载中…</div>
        <div v-else-if="detailError" class="state-box error-box">
          <p class="error-text">{{ detailError }}</p>
          <button class="btn primary" type="button" @click="selectedId !== null && loadDetail(selectedId)">重试</button>
        </div>

        <div v-else-if="detail" class="drawer-body">
          <section class="detail-block">
            <h4>剧本信息</h4>
            <dl class="detail-grid">
              <dt>题材类型</dt><dd>{{ detail.题材类型 || '—' }}</dd>
              <dt>总集数</dt><dd>{{ detail.总集数 || '—' }}</dd>
              <dt>当前版本</dt><dd>{{ detail.当前版本 || '—' }}</dd>
              <dt>定稿日期</dt><dd>{{ detail.定稿日期 || '—' }}</dd>
              <dt>编剧</dt><dd>{{ detail.编剧姓名 || '—' }}</dd>
              <dt>版权归属</dt><dd class="copyright">{{ detail.版权归属 || '—' }}</dd>
            </dl>
          </section>

          <section class="detail-block">
            <h4>审稿记录（{{ detail.审稿记录.length }} 条）</h4>
            <ul v-if="detail.审稿记录.length" class="review-list">
              <li v-for="review in detail.审稿记录" :key="String(review.id)" class="review-item">
                <header class="review-head">
                  <span class="review-round">{{ review.审片轮次 }}</span>
                  <span class="stage-tag review">{{ review.审片状态 }}</span>
                  <time class="review-time">{{ review.审稿时间 }}</time>
                </header>
                <p class="review-line"><em>审稿人：</em>{{ review.审片人 }}</p>
                <p class="review-line"><em>问题类型：</em>{{ review.问题类型 }}</p>
                <p class="review-line"><em>修改意见：</em>{{ review.修改意见 }}</p>
                <p class="review-line"><em>回复说明：</em>{{ review.回复说明 || '—' }}</p>
              </li>
            </ul>
            <!-- 专用空态：区别于读取失败的可重试态 -->
            <div v-else class="state-box empty-review">
              <span class="empty-icon" aria-hidden="true">📝</span>
              <p>这部剧本还没有审稿记录</p>
              <small>提交审稿后，审稿意见会按轮次显示在这里</small>
            </div>
          </section>

          <section class="detail-block">
            <h4>阶段变更时间</h4>
            <ol v-if="detail.阶段变更.length" class="timeline">
              <li v-for="log in detail.阶段变更" :key="String(log.id)" class="timeline-item">
                <span class="timeline-dot" />
                <div class="timeline-body">
                  <p class="timeline-title">
                    <span class="stage-tag ghost-stage">{{ log.原阶段 }}</span>
                    <span aria-hidden="true">→</span>
                    <span :class="['stage-tag', stageClass(log.新阶段)]">{{ log.新阶段 }}</span>
                  </p>
                  <p class="timeline-meta">{{ log.变更时间 }} · {{ log.操作人 }}</p>
                  <p v-if="log.备注" class="timeline-note">{{ log.备注 }}</p>
                </div>
              </li>
            </ol>
            <p v-else class="page-desc">暂无阶段变更记录</p>
          </section>
        </div>
      </aside>
    </div>

    <footer class="page-foot">
      <span>共 {{ total }} 部剧本（含已定稿与已归档）</span>
      <span class="page-desc">列表与看板数据来自同一接口、同一口径</span>
    </footer>
  </section>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'

import { fetchJson } from '@/api/client'

type ScriptSummary = {
  id: number
  剧本编号: string
  剧本名称: string | null
  题材类型: string | null
  总集数: string | number | null
  当前版本: string | null
  定稿日期: string | null
  版权归属: string | null
  编剧姓名: string | null
  推进阶段: string
  审稿记录数: number
  最新审稿状态: string | null
}

type StageLog = {
  id: number
  原阶段: string
  新阶段: string
  变更时间: string
  操作人: string
  备注: string | null
}

type ReviewRecord = {
  id: number
  审稿编号: string
  审片轮次: string
  审片人: string
  问题类型: string
  修改意见: string
  回复说明: string | null
  审片状态: string
  审稿时间: string
}

type ScriptDetail = ScriptSummary & {
  审稿记录: ReviewRecord[]
  阶段变更: StageLog[]
}

type ListResponse = {
  stages: string[]
  total: number
  items: ScriptSummary[]
}

// 列表与看板共用这组概览列，杜绝两边各写一套字段
const columns = ['题材类型', '总集数', '当前版本', '定稿日期'] as const

const mode = ref<'list' | 'board'>('list')
const stages = ref<string[]>([])
const items = ref<ScriptSummary[]>([])
const total = ref(0)
const loading = ref(false)
const loadError = ref('')
const stageFilter = ref('')
const keyword = ref('')

const selectedId = ref<number | null>(null)
const detail = ref<ScriptDetail | null>(null)
const detailOpen = ref(false)
const detailLoading = ref(false)
const detailError = ref('')

const stageCounts = computed(() =>
  stages.value.map((stage) => ({
    stage,
    count: items.value.filter((item) => item.推进阶段 === stage).length,
  })),
)

// 看板按阶段分列；列顺序用后端给的推进阶段顺序，卡片顺序沿用 items，保证与列表一致
const boardColumns = computed(() =>
  stages.value.map((stage) => ({
    name: stage,
    items: items.value.filter((item) => item.推进阶段 === stage),
  })),
)

function resetFilters() {
  stageFilter.value = ''
  keyword.value = ''
  void reload()
}

async function reload() {
  loading.value = true
  loadError.value = ''
  try {
    const params = new URLSearchParams()
    if (stageFilter.value) params.set('stage', stageFilter.value)
    if (keyword.value.trim()) params.set('keyword', keyword.value.trim())
    const query = params.toString()
    const payload = await fetchJson<ListResponse>(`/api/cockpit/scripts${query ? `?${query}` : ''}`)
    stages.value = payload.stages
    items.value = payload.items
    total.value = payload.total
  } catch (error) {
    loadError.value = error instanceof Error ? error.message : '剧本概览读取失败'
    items.value = []
  } finally {
    loading.value = false
  }
}

async function loadDetail(id: number) {
  detailLoading.value = true
  detailError.value = ''
  try {
    detail.value = await fetchJson<ScriptDetail>(`/api/cockpit/scripts/${id}`)
  } catch (error) {
    detail.value = null
    detailError.value = error instanceof Error ? error.message : '审稿详情读取失败'
  } finally {
    detailLoading.value = false
  }
}

async function openDetail(id: number) {
  selectedId.value = id
  detail.value = null
  detailOpen.value = true
  await loadDetail(id)
}

function closeDetail() {
  detailOpen.value = false
}

function stageClass(stage?: string | null): string {
  return {
    创作中: 'stage-writing',
    待审稿: 'stage-reviewing',
    已定稿: 'stage-finalized',
    已归档: 'stage-archived',
  }[stage ?? ''] ?? 'stage-unknown'
}

onMounted(reload)
</script>

<style scoped>
.cockpit .mode-switch {
  display: inline-flex;
  border: 1px solid var(--border);
  border-radius: 6px;
  overflow: hidden;
}
.mode-btn {
  border: none;
  background: #fff;
  padding: 6px 16px;
  cursor: pointer;
  font-size: 13px;
  color: var(--muted);
}
.mode-btn.active {
  background: var(--brand);
  color: #fff;
}
.filter-item select {
  border: 1px solid var(--border);
  border-radius: 6px;
  padding: 5px 8px;
  font-size: 13px;
  min-width: 130px;
}
.state-box {
  background: #fff;
  border: 1px dashed var(--border);
  border-radius: 8px;
  padding: 28px;
  text-align: center;
  color: var(--muted);
  font-size: 13px;
}
.error-box {
  display: flex;
  flex-direction: column;
  gap: 10px;
  align-items: center;
  border-color: #f0a8a0;
}
.clickable-row {
  cursor: pointer;
}
.clickable-row:hover td {
  background: #f4f8ff;
}
tr.selected td {
  background: #e7f0ff;
}
.stage-tag {
  display: inline-block;
  padding: 2px 8px;
  border-radius: 999px;
  font-size: 12px;
  font-style: normal;
  background: #eef2f7;
  color: #475569;
  white-space: nowrap;
}
.stage-writing { background: #e8f0fe; color: #1f4fb0; }
.stage-reviewing { background: #fef3e2; color: #b45309; }
.stage-finalized { background: #e6f7ec; color: #15803d; }
.stage-archived { background: #eef0f3; color: #64748b; }
.stage-tag.review { background: #fdecec; color: #b42318; }
.ghost-stage { background: transparent; border: 1px solid var(--border); }

/* 看板 */
.kanban {
  display: grid;
  grid-auto-flow: column;
  grid-auto-columns: minmax(240px, 1fr);
  gap: 12px;
  align-items: start;
}
.kanban-col {
  background: #eef2f7;
  border: 1px solid var(--border);
  border-radius: 8px;
  padding: 10px;
  display: flex;
  flex-direction: column;
  gap: 8px;
  min-height: 120px;
}
.kanban-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.kanban-count {
  font-size: 12px;
  color: var(--muted);
  background: #fff;
  border-radius: 999px;
  padding: 1px 8px;
}
.kanban-card {
  text-align: left;
  background: #fff;
  border: 1px solid var(--border);
  border-radius: 8px;
  padding: 10px 12px;
  cursor: pointer;
  display: flex;
  flex-direction: column;
  gap: 4px;
  font: inherit;
  color: inherit;
}
.kanban-card:hover { border-color: var(--brand); }
.kanban-card.selected { border-color: var(--brand); box-shadow: 0 0 0 2px rgba(31, 111, 235, 0.15); }
.kanban-title { font-size: 14px; }
.kanban-code { font-size: 12px; color: var(--muted); }
.kanban-meta {
  display: grid;
  grid-template-columns: auto 1fr;
  gap: 3px 10px;
  margin: 6px 0 0;
  font-size: 12px;
}
.kanban-meta dt { color: var(--muted); }
.kanban-meta dd { margin: 0; }
.kanban-empty {
  margin: 0;
  padding: 16px 8px;
  text-align: center;
  color: var(--muted);
  font-size: 12px;
  border: 1px dashed var(--border);
  border-radius: 6px;
  background: rgba(255, 255, 255, 0.6);
}
.page-foot-hint { text-align: center; color: var(--muted); font-size: 12px; }

/* 详情抽屉 */
.drawer-mask {
  position: fixed;
  inset: 0;
  background: rgba(15, 23, 42, 0.35);
  display: flex;
  justify-content: flex-end;
  z-index: 50;
}
.drawer {
  width: 520px;
  max-width: 92vw;
  height: 100%;
  background: #fff;
  box-shadow: -8px 0 24px rgba(15, 23, 42, 0.18);
  display: flex;
  flex-direction: column;
  overflow-y: auto;
}
.drawer-head {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 12px;
  padding: 16px 20px;
  border-bottom: 1px solid var(--border);
  position: sticky;
  top: 0;
  background: #fff;
  z-index: 1;
}
.drawer-head h3 { margin: 0 0 4px; font-size: 16px; }
.drawer-body { padding: 16px 20px; display: flex; flex-direction: column; gap: 20px; }
.detail-block h4 { margin: 0 0 10px; font-size: 14px; }
.detail-grid {
  display: grid;
  grid-template-columns: 84px 1fr;
  gap: 8px 12px;
  margin: 0;
  font-size: 13px;
}
.detail-grid dt { color: var(--muted); }
.detail-grid dd { margin: 0; }
.detail-grid .copyright { color: #1f2937; font-weight: 600; }
.review-list { list-style: none; margin: 0; padding: 0; display: flex; flex-direction: column; gap: 10px; }
.review-item { border: 1px solid var(--border); border-radius: 8px; padding: 10px 12px; }
.review-head { display: flex; align-items: center; gap: 8px; margin-bottom: 6px; }
.review-round { font-weight: 600; font-size: 13px; }
.review-time { margin-left: auto; font-size: 12px; color: var(--muted); }
.review-line { margin: 3px 0; font-size: 13px; }
.review-line em { color: var(--muted); font-style: normal; margin-right: 4px; }
.empty-review { display: flex; flex-direction: column; gap: 4px; align-items: center; padding: 24px; }
.empty-icon { font-size: 26px; }
.empty-review small { color: var(--muted); }

.timeline { list-style: none; margin: 0; padding: 0 0 0 6px; }
.timeline-item { position: relative; padding: 0 0 16px 18px; border-left: 2px solid var(--border); margin-left: 5px; }
.timeline-item:last-child { border-left-color: transparent; padding-bottom: 0; }
.timeline-dot {
  position: absolute;
  left: -7px;
  top: 2px;
  width: 10px;
  height: 10px;
  border-radius: 50%;
  background: var(--brand);
  border: 2px solid #fff;
  box-shadow: 0 0 0 2px var(--brand);
}
.timeline-body { margin-top: -2px; }
.timeline-title { margin: 0 0 4px; display: flex; gap: 6px; align-items: center; }
.timeline-meta { margin: 0 0 2px; font-size: 12px; color: var(--muted); }
.timeline-note { margin: 0; font-size: 12px; }
</style>
