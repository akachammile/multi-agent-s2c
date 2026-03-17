<template>
    <div class="image-preview">
        <img :src="ImageData.slot" alt="" class="image-preview-img">
        <button class="image-preview-close-btn" @click="removeImage">
            <X :size="16" />
        </button>
    </div>
</template>
<script setup lang="ts">
const props = defineProps({
    ImageData: {
        type: Object,
        default: null
    },
})
const emit = defineEmits(['removeImage'])

const removeImage = () => {
    emit("removeImage")
}

</script>
<style scoped>
.image-preview {
    width: 100%;
    height: 100%;
}
.image-preview-img {
    width: 100%;
    height: 100%;
}
.image-preview-close-btn {
    position: absolute;
    top: 0;
    right: 0;
}
</style>