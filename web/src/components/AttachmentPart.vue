<template>
  <div class="attachment-part">
    <label class="attachment-upload" >
      <input
        type="file"
        multiple
        accept=".txt,.md,.docx,.html,.htm"
      />
      <Paperclip :size="14" />
      <span>{{ isUploading ? '上传中…' : '添加附件' }}</span>
    </label>
    
    <div class="attachment-list">
      <div class="attachment-item" v-for="(file, index) in files" :key="index">
        <span class="attachment-name">{{ file.name }}</span>
        <button class="attachment-remove" @click="removeFile(index)">×</button>
      </div>
    </div>
  </div>
</template>
<script setup lang="ts">
import { Paperclip } from "lucide-vue-next"
const props = defineProps({
  isUploading: {
    type: Boolean,
    default: false
  },
  files: {
    type: Object,
    default: () => []
  }
})
const emit = defineEmits(['removeFile', "uploadFile"])

const removeFile = (index: string) => {
  emit('removeFile', index)
}
</script>
<style scoped>

</style>