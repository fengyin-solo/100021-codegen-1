<template>
  <section class="page" data-module="cockpit">
    <header class="page-head">
      <div>
        <h2>剧本审稿驾驶舱</h2>
        <p class="page-desc">
          按推进阶段总览每部剧本的题材类型、总集数、当前版本与定稿日期；点击剧本查看审稿记录、版权归属与阶段变更时间。已归档剧本保留在列，可照常查阅。
        </p>
      </div>
      <div class="page-actions">
        <div class="view-switch" role="tablist" aria-label="视图切换">
          <button
            class="btn"
            :class="{ primary: viewMode === 'board' }"
            type="button"
            @click="viewMode = 'board'"
          >
            看板视图
          </button>
          <button
            class="btn"
            :class="{ primary: viewMode === 'list' }"
            type="button"
            @click="viewMode = 'list'"
          >
            列表视图
          </button>
        </div>
        <button class="btn" type="button" @click="reload">刷新</button>
      </div>
    </header>

    <div v-if="loadError" class="error-panel">
      <span class="error-text">{{ loadError }}</span>
      <button class="btn primary" type="button" @click="reload">重试</button>
    </div>

    <template v-else>
      <div class="stat-row">
        <article v-for="stage in stages" :key="stage" class="stat-card">
          <span class="stat-label">{{ stage }}</span>
          <strong class="stat-value">{{ countByStage(stage) }}</strong>
        </article>
      </div>

      <!-- 看板视图：按推进阶段分列，与列表视图共用同一份 scripts 数据 -->
      <div v-if="viewMode === 'board'" class="board-row">
        <div v-for="stage in stages" :key="stage" class="board-col">
          <header class="board-col-head">{{ stage }} · {{ countByStage(stage) }}</header>
          <article
            v-for="script in scriptsByStage(stage)"
            :key="script.id"
            class="board-card"
            :class="{ active: selectedId === script.id }"
            @click="selectScript(script.id)"
          >
            <strong class="board-card-title">{{ script.剧本名称 }}</strong>
            <span class="board-card-code">{{ script.剧本编号 }}</span>
            <dl class="board-card-fields">
              <div><dt>题材类型</dt><dd>{{ script.题材类型 || '—' }}</dd></div>
              <div><dt>总集数</dt><dd>{{ script.总集数 || '—' }}</dd></div>
              <div><dt>当前版本</dt><dd>{{ script.当前版本 || '—' }}</dd></div>
              <div><dt>定稿日期</dt><dd>{{ script.终稿日期 || '—' }}</dd></div>
            </dl>
          </article>
          <p v-if="!scriptsByStage(stage).length" class="board-empty">该阶段暂无剧本</p>
        </div>
      </div>

      <!-- 列表视图：与看板同一份数据、同一个按阶段排序的口径 -->
      <table v-else class="data-table">
        <thead>
          <tr>
            <th>剧本编号</th>
            <th>剧本名称</th>
            <th>题材类型</th>
            <th>总集数</th>
            <th>当前版本</th>
            <th>定稿日期</th>
            <th>推进阶段</th>
            <th>审稿记录</th>
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="script in scripts"
            :key="script.id"
            class="clickable-row"
            :class="{ active: selectedId === script.id }"
            @click="selectScript(script.id)"
          >
            <td>{{ script.剧本编号 }}</td>
            <td>{{ script.剧本名称 }}</td>
            <td>{{ script.题材类型 || '—' }}</td>
            <td>{{ script.总集数 || '—' }}</td>
            <td>{{ script.当前版本 || '—' }}</td>
            <td>{{ script.终稿日期 || '—' }}</td>
            <td>{{ script.status }}</td>
            <td>{{ script.review_count }} 条</td>
          </tr>
          <tr v-if="!scripts.length && !loading">
            <td colspan="8" class="empty-state">暂无剧本数据</td>
          </tr>
        </tbody>
      </table>

      <p v-if="loading" class="loading-text">驾驶舱数据加载中…</p>

      <!-- 点击剧本后的明细：审稿记录、版权归属、阶段变更时间 -->
      <section v-if="selectedId !== null" class="detail-panel">
        <div v-if="detailError" class="error-panel">
          <span class="error-text">{{ detailError }}</span>
          <button class="btn primary" type="button" @click="retryDetail">重试</button>
        </div>
        <p v-else-if="detailLoading" class="loading-text">审稿明细加载中…</p>
        <template v-else-if="detail">
          <header class="detail-head">
            <div>
              <h3>{{ detail.script.剧本名称 }}（{{ detail.script.剧本编号 }}）</h3>
              <p class="page-desc">
                版权归属：{{ detail.script.版权归属 || '—' }} · 当前阶段：{{ detail.script.status }}
              </p>
            </div>
            <button class="btn ghost" type="button" @click="closeDetail">收起</button>
          </header>

          <div class="detail-grid">
            <section class="detail-block">
              <h4>阶段变更时间</h4>
              <ol class="timeline">
                <li v-for="(item, index) in detail.script.stage_history" :key="index">
                  <span class="timeline-stage">{{ item.stage }}</span>
                  <span class="timeline-at">{{ item.at }}</span>
                </li>
              </ol>
              <p v-if="!detail.script.stage_history.length" class="empty-state">暂无阶段变更记录</p>
            </section>

            <section class="detail-block">
              <h4>审稿记录（{{ detail.review_total }} 条）</h4>
              <div v-if="!detail.reviews.length" class="review-empty">
                <strong>该剧本暂无审稿记录</strong>
                <p>剧本尚未进入审稿流程，或审稿意见尚未登记；可在「审片意见」模块登记后回到这里查看。</p>
              </div>
              <table v-else class="data-table">
                <thead>
                  <tr>
                    <th v-for="column in reviewColumns" :key="column">{{ column }}</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="review in detail.reviews" :key="String(review.id)">
                    <td v-for="column in reviewColumns" :key="column">{{ review[column] || '—' }}</td>
                  </tr>
                </tbody>
              </table>
            </section>
          </div>
        </template>
      </section>
    </template>

    <footer class="page-foot">
      <span>共 {{ total }} 部剧本（含已归档），列表与看板同源展示</span>
    </footer>
  </section>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'

import { fetchJson } from '@/api/client'

type StageChange = { stage: string; at: string }

type ScriptSummary = {
  id: number
  剧本编号: string
  剧本名称: string
  题材类型: string | null
  总集数: string | number | null
  当前版本: string | null
  终稿日期: string | null
  版权归属: string | null
  status: string
  stage_history: StageChange[]
  review_count: number
}

type ReviewRow = Record<string, string | number | null>

type CockpitOverview = {
  stages: string[]
  scripts: ScriptSummary[]
  total: number
}

type CockpitDetail = {
  script: ScriptSummary
  reviews: ReviewRow[]
  review_total: number
}

const ENDPOINT = '/api/cockpit'
const reviewColumns = ['审片编号', '审片轮次', '审片人', '审片对象', '问题类型', '修改意见', '审片状态']

const stages = ref<string[]>([])
const scripts = ref<ScriptSummary[]>([])
const total = ref(0)
const loading = ref(false)
const loadError = ref('')

const viewMode = ref<'board' | 'list'>('board')

const selectedId = ref<number | null>(null)
const detail = ref<CockpitDetail | null>(null)
const detailLoading = ref(false)
const detailError = ref('')

function countByStage(stage: string): number {
  return scripts.value.filter((item) => item.status === stage).length
}

function scriptsByStage(stage: string): ScriptSummary[] {
  // 后端已按推进阶段排好序，这里只按列过滤，不再另起排序口径
  return scripts.value.filter((item) => item.status === stage)
}

async function reload() {
  loading.value = true
  loadError.value = ''
  try {
    const payload = await fetchJson<CockpitOverview>(ENDPOINT)
    stages.value = payload.stages
    scripts.value = payload.scripts
    total.value = payload.total
    if (selectedId.value !== null) {
      if (payload.scripts.some((item) => item.id === selectedId.value)) {
        await loadDetail(selectedId.value)
      } else {
        closeDetail()
      }
    }
  } catch (error) {
    loadError.value = error instanceof Error ? error.message : '驾驶舱数据读取失败，请重试'
  } finally {
    loading.value = false
  }
}

async function loadDetail(scriptId: number) {
  detailLoading.value = true
  detailError.value = ''
  try {
    detail.value = await fetchJson<CockpitDetail>(`${ENDPOINT}/${scriptId}`)
  } catch (error) {
    detail.value = null
    detailError.value = error instanceof Error ? error.message : '审稿明细读取失败，请重试'
  } finally {
    detailLoading.value = false
  }
}

function selectScript(scriptId: number) {
  selectedId.value = scriptId
  void loadDetail(scriptId)
}

function retryDetail() {
  if (selectedId.value !== null) {
    void loadDetail(selectedId.value)
  }
}

function closeDetail() {
  selectedId.value = null
  detail.value = null
  detailError.value = ''
}

onMounted(reload)
</script>
