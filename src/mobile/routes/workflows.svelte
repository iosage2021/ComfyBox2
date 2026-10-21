<script lang="ts">
    import ComfyApp, { type SerializedAppState } from "$lib/components/ComfyApp";
    import workflowState, { ComfyBoxWorkflow, type WorkflowInstID } from "$lib/stores/workflowState";
    import { onMount } from "svelte";
    import interfaceState from "$lib/stores/interfaceState";
    import { vibrateIfPossible } from "$lib/utils";
    import { f7 } from 'framework7-svelte';
    import { XCircle, ArrowClockwise, Download } from 'svelte-bootstrap-icons';

    import { Page, Navbar, NavRight, Link, Button, BlockTitle, Block, List, ListItem, Preloader, Badge } from "framework7-svelte";

    export let app: ComfyApp | null = null;
    let fileInput: HTMLInputElement = undefined;

    interface ServerWorkflowItem {
        filename: string;
        name: string;
        category: string;
        description?: string;
    }

    let serverWorkflows: ServerWorkflowItem[] = [];
    let loadingServerWorkflows = false;
    let searchQuery = "";
    let selectedCategory = "All";

    async function fetchServerWorkflows() {
        loadingServerWorkflows = true;
        try {
            let res = await fetch("/api/workflows");
            if (!res.ok) {
                res = await fetch("/workflows/list.json");
            }
            if (res.ok) {
                const list = await res.json();
                if (Array.isArray(list)) {
                    serverWorkflows = list;
                }
            }
        } catch (e) {
            console.error("Failed to fetch server workflows:", e);
            try {
                const res2 = await fetch("/workflows/list.json");
                if (res2.ok) {
                    serverWorkflows = await res2.json();
                }
            } catch (err) {
                console.error("Fallback list.json failed:", err);
            }
        } finally {
            loadingServerWorkflows = false;
        }
    }

    onMount(() => {
        fetchServerWorkflows();
    });

    $: categories = ["All", ...Array.from(new Set(serverWorkflows.map(w => w.category))).filter(Boolean)];

    $: filteredWorkflows = serverWorkflows.filter(w => {
        const matchCat = selectedCategory === "All" || w.category === selectedCategory;
        const q = searchQuery.trim().toLowerCase();
        const matchSearch = !q || 
            w.name.toLowerCase().includes(q) || 
            (w.description && w.description.toLowerCase().includes(q)) ||
            w.filename.toLowerCase().includes(q);
        return matchCat && matchSearch;
    });

    function getBadgeColor(category: string): string {
        switch (category) {
            case "Qwen Image": return "blue";
            case "MiniMax / Veda": return "purple";
            case "Wan Video": return "green";
            case "FramePack": return "orange";
            case "Templates": return "teal";
            default: return "gray";
        }
    }

    async function onClickLoadServerWorkflow(item: ServerWorkflowItem) {
        vibrateIfPossible(20);
        try {
            f7.preloader.show();
            const wf = await app.loadServerWorkflow(item.filename);
            f7.preloader.hide();
            
            f7.toast.create({
                text: `已加载: ${item.name}`,
                closeTimeout: 2000,
            }).open();

            // Automatically navigate to the newly opened workflow
            const newIndex = $workflowState.openedWorkflows.findIndex(w => w.id === wf.id);
            if (newIndex >= 0) {
                f7.view.main.router.navigate(`/workflows/${newIndex + 1}/`);
            }
        } catch (err) {
            f7.preloader.hide();
            console.error("Error loading server workflow:", err);
            f7.dialog.alert(`加载失败: ${(err as any)?.message || err}`, "错误");
        }
    }

    async function doLoadDefault() {
        f7.dialog.confirm("Would you like to load the default workflow in a new tab?", async () => {
            await app.initDefaultWorkflow();
            app.saveStateToLocalStorage(false);
            const newIndex = $workflowState.openedWorkflows.length;
            f7.view.main.router.navigate(`/workflows/${newIndex}/`);
        });
    }

    function onClickDelete(workflow: ComfyBoxWorkflow, e: Event) {
        e.preventDefault();
        e.stopImmediatePropagation();
        f7.dialog.confirm("Are you sure you want to delete this workflow?", workflow.attrs.title || `Workflow: ${workflow.id}`,
            () => {
                app.closeWorkflow(workflow.id);
                app.saveStateToLocalStorage(false);
            }
        );
    }

    function doLoad(): void {
        if (!fileInput)
            return;

        vibrateIfPossible(20);
        fileInput.value = null;
        fileInput.click();
    }

    function loadWorkflow(): void {
        app.handleFile(fileInput.files[0]);
    }

    function onPageBeforeIn() {
        $interfaceState.selectedWorkflowIndex = null;
        $interfaceState.selectedTab = 1;
        if (serverWorkflows.length === 0) {
            fetchServerWorkflows();
        }
    }
</script>

<Page name="home" on:pageBeforeIn={onPageBeforeIn}>
    <Navbar title="工作流列表 / Workflows">
        <NavRight>
            <Link icon="icon-reload" on:click={fetchServerWorkflows}>
                <ArrowClockwise width="1.4em" height="1.4em" />
            </Link>
        </NavRight>
    </Navbar>

    <BlockTitle>已打开的工作流 ({$workflowState.openedWorkflows ? $workflowState.openedWorkflows.length : 0})</BlockTitle>
    {#if $workflowState.openedWorkflows && $workflowState.openedWorkflows.length > 0}
        <List strong inset dividersIos class="components-list searchbar-found">
            {#each $workflowState.openedWorkflows as workflow, i}
                <ListItem link="/workflows/{i+1}/" transition="f7-cover" title={workflow.attrs.title || `Workflow: ${workflow.id}`}>
                    <svelte:fragment slot="media">
                        <div on:pointerdown={(e) => onClickDelete(workflow, e)} style="cursor: pointer; padding: 4px;">
                            <XCircle width="1.4em" height="1.4em" color="var(--f7-color-red)" />
                        </div>
                    </svelte:fragment>
                </ListItem>
            {/each}
        </List>
    {:else}
        <Block strong inset style="text-align: center; color: var(--f7-text-color-secondary); padding: 14px 16px;">
            暂无已打开的工作流，请从下方选择加载
        </Block>
    {/if}

    <BlockTitle medium>服务器工作流 (点击即可装载)</BlockTitle>

    <!-- Search filter and Category chips -->
    <Block strong inset style="padding: 10px 12px; margin-bottom: 8px;">
        <input 
            type="text" 
            bind:value={searchQuery} 
            placeholder="🔍 搜索工作流 (如 qwen, minimax, wan)..." 
            style="width: 100%; padding: 8px 12px; border-radius: 8px; border: 1px solid rgba(128,128,128,0.25); background: var(--f7-input-bg-color, transparent); color: inherit; font-size: 14px; box-sizing: border-box;"
        />
        {#if categories.length > 2}
            <div style="display: flex; gap: 6px; overflow-x: auto; margin-top: 8px; padding-bottom: 2px;">
                {#each categories as cat}
                    <Button 
                        small 
                        round 
                        fill={selectedCategory === cat} 
                        outline={selectedCategory !== cat} 
                        onClick={() => selectedCategory = cat}
                        style="flex-shrink: 0;"
                    >
                        {cat}
                    </Button>
                {/each}
            </div>
        {/if}
    </Block>

    {#if loadingServerWorkflows}
        <Block style="text-align: center; padding: 24px;">
            <Preloader color="blue" />
            <p style="margin-top: 10px; font-size: 13px; color: var(--f7-text-color-secondary);">正在加载服务器工作流列表...</p>
        </Block>
    {:else if filteredWorkflows.length > 0}
        <List strong inset dividersIos mediaList>
            {#each filteredWorkflows as item}
                <ListItem
                    link="#"
                    title={item.name}
                    badge={item.category}
                    badgeColor={getBadgeColor(item.category)}
                    footer={item.description || item.filename}
                    onClick={() => onClickLoadServerWorkflow(item)}
                >
                    <svelte:fragment slot="media">
                        <Download width="1.3em" height="1.3em" style="margin-top: 4px; color: var(--f7-theme-color);" />
                    </svelte:fragment>
                </ListItem>
            {/each}
        </List>
    {:else}
        <Block strong inset style="text-align: center; color: var(--f7-text-color-secondary); padding: 16px;">
            未找到匹配的工作流
        </Block>
    {/if}

    <Block strong inset>
        <p class="grid grid-cols-2 grid-gap">
            <Button outline onClick={doLoadDefault}>加载测试模板</Button>
            <Button outline onClick={doLoad}>从手机文件选择...</Button>
        </p>
    </Block>
    <input bind:this={fileInput} id="comfy-file-input" style:display="none" type="file" accept=".json" on:change={loadWorkflow} />
</Page>
