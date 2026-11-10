<script lang="ts">
    import type { WidgetLayout } from "$lib/stores/layoutStates";
    import type ComfyAudioNode from "$lib/nodes/widgets/ComfyAudioNode";
    import { convertComfyOutputToComfyURL, type ComfyImageLocation } from "$lib/utils";
    import type { Writable } from "svelte/store";

    export let widget: WidgetLayout | null = null;
    export let isMobile: boolean = false;

    let node: ComfyAudioNode | null = null;
    let nodeValue: Writable<ComfyImageLocation[]> | null = null;

    $: if (widget) {
        node = widget.node as ComfyAudioNode;
        nodeValue = node.value;
    }

    function getAudioUrl(audio: ComfyImageLocation): string {
        return convertComfyOutputToComfyURL(audio);
    }
</script>

<div class="comfy-audio-widget" class:mobile={isMobile}>
    {#if $nodeValue && $nodeValue.length > 0}
        <div class="audio-list">
            {#each $nodeValue as audio}
                <div class="audio-card">
                    <div class="audio-info">
                        <span class="audio-icon">🎵</span>
                        <span class="audio-name" title={audio.filename}>{audio.filename}</span>
                        <a
                            class="audio-download-link"
                            href={getAudioUrl(audio)}
                            download={audio.filename}
                            title="Download audio"
                            target="_blank"
                            rel="noopener"
                        >
                            ⬇️
                        </a>
                    </div>
                    <audio
                        class="native-audio"
                        controls
                        preload="metadata"
                        src={getAudioUrl(audio)}
                    >
                        Your browser does not support the audio element.
                    </audio>
                </div>
            {/each}
        </div>
    {:else}
        <div class="audio-empty">
            <span class="empty-icon">🎵</span>
            <span class="empty-text">(Waiting for audio output...)</span>
        </div>
    {/if}
</div>

<style lang="scss">
    .comfy-audio-widget {
        width: 100%;
        padding: 6px;
        box-sizing: border-box;

        &.mobile {
            padding: 8px 4px;
        }
    }

    .audio-list {
        display: flex;
        flex-direction: column;
        gap: 10px;
    }

    .audio-card {
        display: flex;
        flex-direction: column;
        gap: 8px;
        padding: 10px 12px;
        border-radius: 8px;
        background: var(--input-background-fill, rgba(255, 255, 255, 0.05));
        border: 1px solid var(--input-border-color, rgba(128, 128, 128, 0.25));
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.12);
        transition: border-color 0.2s ease;

        &:hover {
            border-color: var(--color-teal-500, #0d9488);
        }
    }

    .audio-info {
        display: flex;
        align-items: center;
        gap: 8px;
        overflow: hidden;
    }

    .audio-icon {
        font-size: 16px;
        flex-shrink: 0;
    }

    .audio-name {
        flex: 1;
        font-size: 13px;
        font-weight: 500;
        color: var(--body-text-color, inherit);
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
    }

    .audio-download-link {
        flex-shrink: 0;
        text-decoration: none;
        font-size: 14px;
        padding: 2px 6px;
        border-radius: 4px;
        background: rgba(128, 128, 128, 0.15);
        cursor: pointer;
        transition: background 0.15s ease;

        &:hover {
            background: rgba(128, 128, 128, 0.3);
        }
    }

    .native-audio {
        width: 100%;
        height: 38px;
        border-radius: 6px;
        outline: none;
    }

    .audio-empty {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        gap: 6px;
        padding: 24px 12px;
        color: var(--f7-text-color-secondary, var(--neutral-400, #888));
        background: rgba(0, 0, 0, 0.03);
        border: 1px dashed var(--input-border-color, rgba(128, 128, 128, 0.25));
        border-radius: 8px;

        .empty-icon {
            font-size: 24px;
            opacity: 0.6;
        }

        .empty-text {
            font-size: 13px;
        }
    }
</style>
