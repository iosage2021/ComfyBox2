<script lang="ts">
 import { tick } from 'svelte'
 import { BlockTitle } from "@gradio/atoms";
 import Select from 'svelte-select';
 // import VirtualList from '$lib/components/VirtualList.svelte';
 import VirtualList from 'svelte-tiny-virtual-list';
 import type { ComfyComboNode } from "$lib/nodes/widgets";
 import { type WidgetLayout } from "$lib/stores/layoutStates";
 import { get, writable, type Writable } from "svelte/store";
 import { isDisabled } from "./utils"
 import { clamp, getSafetensorsMetadata, vibrateIfPossible, batchUploadBlobsToComfyUI } from '$lib/utils';
 import configState from '$lib/stores/configState';
 import notify from '$lib/notify';
 export let widget: WidgetLayout | null = null;
 export let isMobile: boolean = false;
 let node: ComfyComboNode | null = null;
 let nodeValue: Writable<string> = writable("");
 let propsChanged: Writable<number> | null = null;
 let lightUp: Writable<boolean> = writable(false);
 let valuesForCombo: Writable<any[]> = writable([])
 let lastConfigured: any = null;
 let option: any = null;

 export let debug: boolean = false;
 let input: HTMLInputElement | null = null
 let fileInput: HTMLInputElement | null = null;
 let pasteInputRef: HTMLInputElement | null = null;
 let showPasteBox = false;
 let isUploading = false;

 $: isImageUpload = Boolean(
     node?.properties?.imageUpload ||
     (node?.properties?.values && node.properties.values.some(v => typeof v === 'string' && /\.(png|jpe?g|webp|gif|bmp)$/i.test(v)))
 );

 async function uploadImageBlob(blob: Blob, originalFilename?: string) {
     isUploading = true;
     try {
         const ext = blob.type.split("/")[1]?.replace("+xml", "") || "png";
         const filename = originalFilename || `paste_${Date.now()}.${ext}`;
         const res = await batchUploadBlobsToComfyUI([{
             blob,
             filename,
             overwrite: true
         }]);
         if (res.files && res.files.length > 0) {
             const uploadedName = res.files[0].filename;
             if (!$valuesForCombo.some(v => v.value === uploadedName)) {
                 $valuesForCombo = [{ value: uploadedName, label: uploadedName, index: $valuesForCombo.length }, ...$valuesForCombo];
             }
             $nodeValue = uploadedName;
             if (node) {
                 node.setValue(uploadedName);
                 if (!node.properties.values.includes(uploadedName)) {
                     node.properties.values.unshift(uploadedName);
                 }
             }
             notify(`图片已载入: ${uploadedName}`, { type: "info" });
         } else if (res.errors && res.errors.length > 0) {
             notify(`上传失败: ${res.errors.join(', ')}`, { type: "error" });
         }
     } catch (err: any) {
         notify(`上传失败: ${err?.message || err}`, { type: "error" });
     } finally {
         isUploading = false;
     }
 }

 async function onFileSelected(e: Event) {
     const target = e.target as HTMLInputElement;
     if (!target.files || target.files.length === 0) return;
     const file = target.files[0];
     try {
         await uploadImageBlob(file, file.name);
     } finally {
         target.value = "";
     }
 }

 async function pasteFromClipboard() {
     if (isUploading) return;

     // 1. Try standard async clipboard API first
     if (navigator.clipboard && navigator.clipboard.read) {
         try {
             const items = await navigator.clipboard.read();
             for (const item of items) {
                 const imageType = item.types.find(t => t.startsWith("image/"));
                 if (imageType) {
                     const blob = await item.getType(imageType);
                     const ext = imageType.split("/")[1] || "png";
                     const filename = `paste_${Date.now()}.${ext}`;
                     await uploadImageBlob(blob, filename);
                     return;
                 }
             }
             notify("剪贴板中未找到图片", { type: "warning" });
             return;
         } catch (err: any) {
             console.warn("navigator.clipboard.read failed, falling back to manual paste box:", err);
         }
     }

     // 2. Fallback for non-secure HTTP / mobile browser restriction:
     // Show paste-catcher input box so user can long-press and paste
     showPasteBox = true;
     await tick();
     pasteInputRef?.focus();
     notify("请在下方输入框长按并选择「粘贴」，或直接按 Ctrl+V", { type: "info" });
 }

 function handlePaste(e: ClipboardEvent) {
     if (!isImageUpload) return;
     const clipboardData = e.clipboardData;
     if (!clipboardData) return;

     let foundImage = false;

     if (clipboardData.items) {
         for (let i = 0; i < clipboardData.items.length; i++) {
             const item = clipboardData.items[i];
             if (item.type.startsWith("image/")) {
                 const file = item.getAsFile();
                 if (file) {
                     e.preventDefault();
                     e.stopPropagation();
                     const ext = file.type.split("/")[1] || "png";
                     const filename = `paste_${Date.now()}.${ext}`;
                     showPasteBox = false;
                     uploadImageBlob(file, filename);
                     foundImage = true;
                     break;
                 }
             }
         }
     }

     if (!foundImage && clipboardData.files && clipboardData.files.length > 0) {
         for (let i = 0; i < clipboardData.files.length; i++) {
             const file = clipboardData.files[i];
             if (file.type.startsWith("image/")) {
                 e.preventDefault();
                 e.stopPropagation();
                 showPasteBox = false;
                 uploadImageBlob(file, file.name);
                 foundImage = true;
                 break;
             }
         }
     }
 }

 function handleDrop(e: DragEvent) {
     if (!isImageUpload) return;
     if (e.dataTransfer && e.dataTransfer.files && e.dataTransfer.files.length > 0) {
         for (let i = 0; i < e.dataTransfer.files.length; i++) {
             const file = e.dataTransfer.files[i];
             if (file.type.startsWith("image/")) {
                 e.preventDefault();
                 e.stopPropagation();
                 uploadImageBlob(file, file.name);
                 break;
             }
         }
     }
 }

 $: widget && setNodeValue(widget);

 $: if (nodeValue !== null) {
     // if (option == null || node.properties.values.indexOf(option.value) === -1) {
     //     setOption($nodeValue)
     //     $nodeValue = option
     // }
     // else {
     //     $nodeValue = option
     //     setOption($nodeValue)
     // }
     setNodeValue(widget)
     node.properties = node.properties
 }

 function setNodeValue(widget: WidgetLayout) {
     if(widget) {
         node = widget.node as ComfyComboNode
         nodeValue = node.value;
         propsChanged = node.propsChanged;
         lightUp = node.lightUp;
         valuesForCombo = node.valuesForCombo;
         lastConfigured = $valuesForCombo
     }
 }

 $: $valuesForCombo != null && updateActiveIndex($valuesForCombo)

 function updateActiveIndex(values: any) {
     const value = $nodeValue;
     activeIndex = values.findIndex(v => v.value === value);
 }

 $: if ($lightUp)
     setTimeout(() => ($lightUp = false), 1000);

 function getLinkValue() {
     if (!node)
         return "???";
     const links = node.getOutputLinks(0)
     if (links.length === 0)
         return "???";
     return links[0].data
 }

 function onFocus() {
     // console.warn("FOCUS")
     if (listOpen) {
         vibrateIfPossible(20)
     }
 }

 let activeIndex = null;
 let hoverItemIndex = null;
 let filterText = "";
 let listOpen = null;

 function handleHover(index: number) {
     // console.warn("HOV", index)
     hoverItemIndex = index;
 }

 function handleSelect(index: number) {
     // console.warn("SEL", index)
     vibrateIfPossible(20)
     const item = $valuesForCombo[index]
     activeIndex = index;
     $nodeValue = item.value
     listOpen = false;
     filterText = ""
     setTimeout(() => {
         input?.blur();
     }, 100)
 }

 function onFilter() {
     // if (scrollToIndex)
     //     scrollToIndex(0)
 }

 const activeScroll = scrollAction;
 const hoverScroll = scrollAction;

 function scrollAction(node) {
     return {
         update(args) {
             if (args.scroll) {
                 // handleListScroll();
                 node.scrollIntoView({ behavior: 'auto', block: 'nearest' });
             }
         },
     };
 }

 let title: ""

 $: nodeValue && $nodeValue && (title = getTitle($nodeValue))

 function getTitle(value?: string) {
     if (value == null) {
         if (!nodeValue)
             return ""
         value = $nodeValue
     }

     if (value && value.length > 80)
         return String(value)
     return ""
 }
</script>

<div 
    class="wrapper comfy-combo" 
    class:mobile={isMobile} 
    class:updated={$lightUp}
    tabindex="0"
    on:paste={handlePaste}
    on:dragover|preventDefault
    on:drop={handleDrop}
>
    <label title={title}>
        {#if widget.attrs.title !== ""}
            <div class="combo-header">
                <BlockTitle show_label={true}>
                    {widget.attrs.title}
                    <span class="count-text">({$valuesForCombo.length})</span>
                </BlockTitle>
                {#if isImageUpload}
                    <div class="combo-actions">
                        <button 
                            type="button" 
                            class="combo-btn paste-btn" 
                            disabled={isUploading}
                            title="从剪贴板粘贴图片 (Ctrl+V)"
                            on:click|preventDefault|stopPropagation={pasteFromClipboard}
                        >
                            📋 粘贴
                        </button>
                        <button 
                            type="button" 
                            class="combo-btn upload-btn" 
                            disabled={isUploading}
                            title="选择本地或相册图片上传"
                            on:click|preventDefault|stopPropagation={() => fileInput?.click()}
                        >
                            {isUploading ? "上传中..." : "📷 上传"}
                        </button>
                    </div>
                    <input 
                        type="file" 
                        accept="image/*" 
                        bind:this={fileInput} 
                        style="display: none;" 
                        on:change={onFileSelected} 
                    />
                {/if}
            </div>
        {:else if isImageUpload}
            <div class="combo-header" style="justify-content: flex-end;">
                <div class="combo-actions">
                    <button 
                        type="button" 
                        class="combo-btn paste-btn" 
                        disabled={isUploading}
                        title="从剪贴板粘贴图片 (Ctrl+V)"
                        on:click|preventDefault|stopPropagation={pasteFromClipboard}
                    >
                        📋 粘贴
                    </button>
                    <button 
                        type="button" 
                        class="combo-btn upload-btn" 
                        disabled={isUploading}
                        title="选择本地或相册图片上传"
                        on:click|preventDefault|stopPropagation={() => fileInput?.click()}
                    >
                        {isUploading ? "上传中..." : "📷 上传"}
                    </button>
                </div>
                <input 
                    type="file" 
                    accept="image/*" 
                    bind:this={fileInput} 
                    style="display: none;" 
                    on:change={onFileSelected} 
                />
            </div>
        {/if}
        {#if isImageUpload && showPasteBox}
            <div class="paste-box-container">
                <input 
                    type="text" 
                    class="paste-box-input" 
                    bind:this={pasteInputRef} 
                    placeholder="👉 在此长按选择「粘贴」，或按 Ctrl+V"
                    on:paste={handlePaste} 
                    on:blur={() => setTimeout(() => showPasteBox = false, 300)}
                />
                <button type="button" class="paste-box-close" on:click={() => showPasteBox = false}>✕</button>
            </div>
        {/if}
        <Select
            value={$valuesForCombo.length === 0 ? "(Loading...)" : $nodeValue}
            bind:justValue={option}
            bind:hoverItemIndex
            bind:filterText
            bind:listOpen
            bind:input
            items={$valuesForCombo}
            disabled={$valuesForCombo.length === 0 || isDisabled(widget)}
            clearable={false}
            showChevron={true}
            listAutoWidth={true}
            inputAttributes={{ autocomplete: 'off' }}
            on:change
            on:focus={onFocus}
            on:hoverItem={(e) => handleHover(e.detail)}
            on:select={(e) => handleSelect(e.detail.index)}
            on:blur
            on:filter={onFilter}>
            <div class="comfy-select-list" slot="list"
                 class:mobile={isMobile}
                 let:filteredItems
                 style:--maxLabelWidth={node.maxLabelWidthChars || 100}>
                {#if filteredItems.length > 0}
                    {@const itemSize = isMobile ? 50 : 25}
                    {@const itemsToShow = isMobile ? 10 : 30}
                    <VirtualList
                        items={filteredItems}
                        width="100%"
                        height={Math.min(filteredItems.length, itemsToShow) * itemSize}
                        itemCount={filteredItems.length}
                        {itemSize}
                        overscanCount={5}
                        scrollToIndex={activeIndex != null ? clamp(activeIndex + itemsToShow - 1, 0, filteredItems.length-1) : hoverItemIndex}>
                        <div slot="item"
                                class="comfy-select-item"
                                class:mobile={isMobile}
                                let:index={i}
                                let:style
                                title={getTitle(filteredItems[i].label)}
                                {style}
                                class:active={activeIndex === filteredItems[i].index}
                                class:hover={hoverItemIndex === i}
                                on:click={() => handleSelect(filteredItems[i].index)}
                            on:focus={() => handleHover(i)}
                            on:mouseover={() => handleHover(i)}>
                            {@const item = filteredItems[i]}
                            <span class="comfy-select-label">
                                {item.label}
                            </span>
                        </div>
                    </VirtualList>
                {:else}
                    <div class="comfy-empty-list">
                        <span>(No items)</span>
                    </div>
                {/if}
            </div>
        </Select>
        {#if isImageUpload && $nodeValue && !['', '(Loading...)', 'None', '(No items)'].includes($nodeValue)}
            <div class="combo-image-preview">
                <img 
                    src="{configState.getBackendURL()}/view?filename={encodeURIComponent($nodeValue)}&type=input" 
                    alt={$nodeValue} 
                    on:error={(e) => { const el = e.currentTarget; if (el instanceof HTMLElement) el.style.display = 'none'; }} 
                />
            </div>
        {/if}
    </label>
</div>

<style lang="scss">
 .combo-header {
     display: flex;
     justify-content: space-between;
     align-items: center;
     margin-bottom: 4px;
 }

 .combo-actions {
     display: flex;
     gap: 6px;
     align-items: center;
 }

 .combo-btn {
     border: none;
     border-radius: 4px;
     padding: 3px 8px;
     font-size: 12px;
     cursor: pointer;
     display: inline-flex;
     align-items: center;
     gap: 3px;
     transition: all 0.15s ease;

     &:hover {
         opacity: 0.88;
         transform: translateY(-1px);
     }
     &:active {
         transform: translateY(0);
     }
     &:disabled {
         opacity: 0.5;
         cursor: not-allowed;
     }
 }

 .paste-btn {
     background: var(--color-teal-500, #0d9488);
     color: white;
 }

 .upload-btn {
     background: var(--color-primary-500, #3b82f6);
     color: white;
 }

 .paste-box-container {
     display: flex;
     gap: 4px;
     margin-bottom: 6px;
     animation: fade-in 0.2s ease-out;
 }

 .paste-box-input {
     flex: 1;
     padding: 6px 10px;
     border-radius: 6px;
     border: 2px dashed var(--color-teal-500, #0d9488);
     background: rgba(13, 148, 136, 0.08);
     font-size: 13px;
     color: inherit;
     outline: none;

     &::placeholder {
         color: var(--color-teal-600, #0f766e);
         font-size: 12px;
     }
 }

 .paste-box-close {
     background: transparent;
     border: none;
     color: var(--f7-text-color-secondary, #888);
     cursor: pointer;
     padding: 0 6px;
     font-size: 14px;
     &:hover {
         color: var(--f7-color-red, #ef4444);
     }
 }

 .combo-image-preview {
     margin-top: 6px;
     border-radius: 6px;
     overflow: hidden;
     border: 1px solid rgba(128, 128, 128, 0.2);
     max-height: 180px;
     display: flex;
     align-items: center;
     justify-content: center;
     background: rgba(0, 0, 0, 0.05);
     cursor: pointer;
     transition: border-color 0.2s ease;

     &:hover {
         border-color: var(--color-teal-500, #0d9488);
     }

     img {
         max-width: 100%;
         max-height: 180px;
         object-fit: contain;
         display: block;
     }
 }

 .wrapper {
     padding: 2px;
     width: 100%;

     .count-text {
         font-size: smaller;
     }

     :global(.selected-item) {
         // no idea how to get the select box to shrink in the flexbox otherwise...
         position: absolute !important;
         width: -webkit-fill-available !important;
     }
 }

 @keyframes -global-light-up {
     from {
         background-color: var(--color-yellow-400);
     }
     to {
         background-color: none;
     }
 }

 .updated {
     animation: light-up 1s ease-out;
     :global(.svelte-select) {
         animation: light-up 1s ease-out;
     }
 }

 :global(.svelte-select) {
     width: auto;
     --font-size: 13px;
     --height: 32px;
     --background: var(--input-background-fill);
     --selected-item-color: var(--body-text-color);
     --input-color: var(--body-text-color);
     --chevron-color: var(--body-text-color);
     --border: 1px solid var(--input-border-color);
     --border-hover: 1px solid var(--input-border-color-hover);
     --border-focused: 1px solid var(--neutral-400);
     --border-radius-focused: 0px;
     --border-radius: 0px;
     --list-background: var(--comfy-dropdown-list-background);
     --item-border: var(--comfy-dropdown-border-color);
     --item-color: var(--body-text-color);
     --item-color-hover: var(--comfy-dropdown-item-color-hover);
     --item-background-hover: var(--comfy-dropdown-item-background-hover);
     --item-color-active: var(--comfy-dropdown-item-color-active);
     --item-background-active: var(--comfy-dropdown-item-background-active);
     --disabled-color: var(--comfy-disabled-textbox-text-color);
     --disabled-border-color: var(--comfy-disabled-textbox-border-color);
     --disabled-background: var(--comfy-disabled-textbox-background-fill);
 }


 :global(.svelte-select.disabled) {
     --input-color: var(--comfy-disabled-textbox-text-color) !important;
     --selected-item-color: var(--comfy-disabled-textbox-text-color) !important;
 }

 :global(.svelte-select-list) {
     z-index: var(--layer-top) !important;
     overflow-y: initial !important;
     width: auto !important; // seems floating-ui overrides listAutoWidth
 }

 .container {
     border-top: 1px solid #333;
     border-bottom: 1px solid #333;

     height: 100%
 }

 .comfy-select-list {
     --maxLabelWidth: 100;
     --maxListWidth: 50vw;
     &.mobile {
         --maxListWidth: 80vw;
     }

     font-size: 14px;
     color: var(--item-color);
     width: min(calc((var(--maxLabelWidth) + 10) * 1ch), var(--maxListWidth));

     > :global(.virtual-list-wrapper) {
         box-shadow: var(--block-shadow);
         background-color: var(--list-background);
     }

     .comfy-empty-list {
         height: 100%;
         display: flex;
         justify-content: center;
         align-items: center;
         font-size: xx-large;
         color: var(--neutral-400)
     }

     .comfy-select-item {
         border: 1px solid var(--item-border);
         border-top: none;
         white-space: nowrap;
         overflow: hidden;
         text-overflow: ellipsis;
         display: flex;
         align-items: center;
         background-color: var(--list-background);

         font-size: 14px;
         padding: 0.2rem;

         .comfy-select-label {
         }

         &.mobile {
             font-size: 16px;
             padding: 1.2rem;
         }

         &.hover {
             color: var(--item-color-hover);
             background: var(--item-background-hover);
             cursor: pointer;
         }
         &.active {
             color: var(--item-color-active);
             background: var(--item-background-active);
         }
     }

     .details {
         background: white;
         border: 1px solid grey;
     }

     :global(svelte-virtual-list-row) {
         white-space: nowrap;
     }
 }
</style>
