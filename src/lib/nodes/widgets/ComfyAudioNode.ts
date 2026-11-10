import { isComfyImageLocation, type ComfyImageLocation } from "$lib/utils";
import { BuiltInSlotType, LiteGraph, type SlotLayout, type SerializedLGraphNode } from "@litegraph-ts/core";
import { get } from "svelte/store";

import AudioWidget from "$lib/widgets/AudioWidget.svelte";
import type { ComfyWidgetProperties } from "./ComfyWidgetNode";
import ComfyWidgetNode from "./ComfyWidgetNode";

export interface ComfyAudioProperties extends ComfyWidgetProperties {
    autoPlay: boolean;
}

export default class ComfyAudioNode extends ComfyWidgetNode<ComfyImageLocation[]> {
    override properties: ComfyAudioProperties = {
        tags: [],
        defaultValue: [],
        autoPlay: false
    }

    static slotLayout: SlotLayout = {
        inputs: [
            { name: "audio", type: "OUTPUT" },
            { name: "store", type: BuiltInSlotType.ACTION, options: { color_off: "rebeccapurple", color_on: "rebeccapurple" } }
        ],
        outputs: [
            { name: "audio", type: "COMFYBOX_AUDIO" }
        ]
    }

    override svelteComponentType = AudioWidget;
    override defaultValue = [];
    override saveUserState = false;
    override outputSlotName = null;
    override changedEventName = null;
    override storeActionName = "store";

    constructor(name?: string) {
        super(name, []);
        this.defaultValue = [];
    }

    override onExecute() {
        const value = get(this.value);
        this.setOutputData(0, value);
    }

    override formatValue(value: ComfyImageLocation[] | null): string {
        return `Audio: ${value?.length || 0}`;
    }

    override stripUserState(o: SerializedLGraphNode) {
        super.stripUserState(o);
        o.properties.defaultValue = [];
        (o as any).comfyValue = [];
    }

    override parseValue(param: any): ComfyImageLocation[] {
        if (!param) return [];
        if (typeof param === "object" && Array.isArray(param.audio)) {
            return param.audio.filter(isComfyImageLocation);
        }
        if (Array.isArray(param)) {
            return param.filter(isComfyImageLocation);
        }
        if (isComfyImageLocation(param)) {
            return [param];
        }
        return [];
    }
}

LiteGraph.registerNodeType({
    class: ComfyAudioNode,
    title: "UI.Audio",
    desc: "Audio player that plays audio outputs natively",
    type: "ui/audio"
});
