<template>
    <slot name="imagePreview"></slot>
    <slot name="attachmentOption"></slot>
    <textarea ref="inputRefs" v-model="inputText">

    </textarea>
    <button>
        <Send :size="14" @click="sendMessage" />
    </button>



</template>

<script setup lang="ts">
import { Send } from "lucide-vue-next";
import type { PropType } from "vue";
const props = defineProps({
    inputText: {
        type: String,
        default: ""
    },
    placeholder: {
        type: String,
        default: ""
    },
    files: {
        type: Array as PropType<File[]>,
        default: () => []
    },// 父组件传入
})

const sendMessage = () => {
    if (props.inputText.trim() === "" && props.files.length === 0) {
        return;
    }
    // emit("send", {
    //     text: props.inputText,
    //     files: props.files,
    // });
    // // 清空输入
    // props.inputText = "";
    // props.files = [];

}



</script>