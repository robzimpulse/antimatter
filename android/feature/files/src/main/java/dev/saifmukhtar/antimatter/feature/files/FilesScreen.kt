package dev.saifmukhtar.antimatter.feature.files

import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.*
import androidx.compose.material.icons.automirrored.filled.Article
import androidx.compose.material.icons.automirrored.filled.KeyboardArrowRight
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import dev.saifmukhtar.antimatter.core.network.FileNode
import dev.saifmukhtar.antimatter.feature.files.FilesUiState

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun FilesScreen(
    uiState: FilesUiState,
    onRefresh: () -> Unit,
    onOpenFile: (String) -> Unit,
    onChangeWorkspace: (String) -> Unit
) {
    var expandedFolders by remember { mutableStateOf(setOf<String>()) }

    LaunchedEffect(Unit) {
        if (uiState.fileTree == null && !uiState.isLoadingTree) {
            onRefresh()
        }
    }

    Scaffold(
        topBar = {
            var workspaceDropdownExpanded by remember { mutableStateOf(false) }

            TopAppBar(
                title = {
                    Row(
                        modifier = Modifier.fillMaxWidth(),
                        verticalAlignment = Alignment.CenterVertically
                    ) {
                        // ── Left: screen title ─────────────────────────────────
                        Text("Workspace", fontWeight = FontWeight.Bold)

                        Spacer(modifier = Modifier.weight(1f))

                        // ── Center-right: workspace switcher chip ──────────────
                        Box {
                            Surface(
                                onClick = {
                                    if (uiState.allowedWorkspaces.size > 1) {
                                        workspaceDropdownExpanded = true
                                    }
                                },
                                shape = RoundedCornerShape(20.dp),
                                color = MaterialTheme.colorScheme.secondaryContainer,
                                modifier = Modifier.height(36.dp)
                            ) {
                                Row(
                                    modifier = Modifier.padding(horizontal = 14.dp),
                                    verticalAlignment = Alignment.CenterVertically,
                                    horizontalArrangement = Arrangement.spacedBy(4.dp)
                                ) {
                                    Icon(
                                        imageVector = Icons.Default.Folder,
                                        contentDescription = null,
                                        tint = MaterialTheme.colorScheme.onSecondaryContainer,
                                        modifier = Modifier.size(16.dp)
                                    )
                                    Text(
                                        text = uiState.currentWorkspace
                                            ?.substringAfterLast("/")
                                            ?.ifBlank { uiState.currentWorkspace }
                                            ?: "No workspace",
                                        style = MaterialTheme.typography.labelLarge,
                                        fontWeight = FontWeight.SemiBold,
                                        color = MaterialTheme.colorScheme.onSecondaryContainer,
                                        maxLines = 1
                                    )
                                    if (uiState.allowedWorkspaces.size > 1) {
                                        Icon(
                                            imageVector = if (workspaceDropdownExpanded)
                                                Icons.Default.KeyboardArrowUp
                                            else
                                                Icons.Default.KeyboardArrowDown,
                                            contentDescription = "Switch workspace",
                                            tint = MaterialTheme.colorScheme.onSecondaryContainer,
                                            modifier = Modifier.size(16.dp)
                                        )
                                    }
                                }
                            }

                            DropdownMenu(
                                expanded = workspaceDropdownExpanded,
                                onDismissRequest = { workspaceDropdownExpanded = false }
                            ) {
                                uiState.allowedWorkspaces.forEach { ws ->
                                    val isActive = ws == uiState.currentWorkspace
                                    DropdownMenuItem(
                                        text = {
                                            Row(
                                                verticalAlignment = Alignment.CenterVertically,
                                                horizontalArrangement = Arrangement.spacedBy(8.dp)
                                            ) {
                                                Icon(
                                                    imageVector = if (isActive) Icons.Default.FolderOpen else Icons.Default.Folder,
                                                    contentDescription = null,
                                                    tint = if (isActive) MaterialTheme.colorScheme.primary
                                                           else MaterialTheme.colorScheme.onSurface,
                                                    modifier = Modifier.size(18.dp)
                                                )
                                                Column {
                                                    Text(
                                                        text = ws.substringAfterLast("/").ifBlank { ws },
                                                        style = MaterialTheme.typography.bodyMedium,
                                                        fontWeight = if (isActive) FontWeight.Bold else FontWeight.Normal,
                                                        color = if (isActive) MaterialTheme.colorScheme.primary
                                                                else MaterialTheme.colorScheme.onSurface
                                                    )
                                                    Text(
                                                        text = ws,
                                                        style = MaterialTheme.typography.labelSmall,
                                                        color = MaterialTheme.colorScheme.onSurfaceVariant
                                                    )
                                                }
                                            }
                                        },
                                        onClick = {
                                            workspaceDropdownExpanded = false
                                            onChangeWorkspace(ws)
                                        },
                                        trailingIcon = if (isActive) {
                                            { Icon(Icons.Default.Check, contentDescription = null, tint = MaterialTheme.colorScheme.primary, modifier = Modifier.size(16.dp)) }
                                        } else null
                                    )
                                }
                            }
                        }

                        Spacer(modifier = Modifier.width(4.dp))
                    }
                },
                colors = TopAppBarDefaults.topAppBarColors(
                    containerColor = MaterialTheme.colorScheme.surface.copy(alpha = 0.8f)
                ),
                actions = {
                    IconButton(onClick = onRefresh) {
                        Icon(
                            Icons.Default.Refresh,
                            contentDescription = "Refresh",
                            tint = MaterialTheme.colorScheme.primary
                        )
                    }
                }
            )
        },
        containerColor = MaterialTheme.colorScheme.background

    ) { paddingValues ->
        Box(
            modifier = Modifier
                .fillMaxSize()
                .padding(paddingValues)
        ) {
            if (uiState.isLoadingTree) {
                CircularProgressIndicator(modifier = Modifier.align(Alignment.Center))
            } else if (uiState.fileTree.isNullOrEmpty()) {
                Column(
                    modifier = Modifier.align(Alignment.Center),
                    horizontalAlignment = Alignment.CenterHorizontally
                ) {
                    Icon(
                        Icons.Default.FolderOff,
                        contentDescription = null,
                        modifier = Modifier.size(48.dp),
                        tint = MaterialTheme.colorScheme.onSurfaceVariant.copy(alpha = 0.5f)
                    )
                    Spacer(modifier = Modifier.height(16.dp))
                    Text(
                        text = "No files found",
                        style = MaterialTheme.typography.titleMedium,
                        color = MaterialTheme.colorScheme.onSurfaceVariant
                    )
                }
            } else {
                LazyColumn(
                    modifier = Modifier.fillMaxSize(),
                    contentPadding = PaddingValues(top = 8.dp, bottom = 80.dp, start = 16.dp, end = 16.dp),
                    verticalArrangement = Arrangement.spacedBy(8.dp)
                ) {
                    items(uiState.fileTree) { node ->
                        FileTreeNode(
                            node = node,
                            depth = 0,
                            expandedFolders = expandedFolders,
                            onToggleFolder = { path ->
                                expandedFolders = if (expandedFolders.contains(path)) {
                                    expandedFolders - path
                                } else {
                                    expandedFolders + path
                                }
                            },
                            onOpenFile = onOpenFile
                        )
                    }
                }
            }
        }
    }
}

@Composable
fun FileTreeNode(
    node: FileNode,
    depth: Int,
    expandedFolders: Set<String>,
    onToggleFolder: (String) -> Unit,
    onOpenFile: (String) -> Unit
) {
    val isExpanded = expandedFolders.contains(node.path)
    val isTopLevel = depth == 0

    val content = @Composable {
        Row(
            modifier = Modifier
                .fillMaxWidth()
                .clickable {
                    if (node.isDir) {
                        onToggleFolder(node.path)
                    } else {
                        onOpenFile(node.path)
                    }
                }
                .padding(vertical = 12.dp, horizontal = 16.dp)
                .padding(start = (depth * 24).dp),
            verticalAlignment = Alignment.CenterVertically
        ) {
            val (icon, tint) = getIconForNode(node, isExpanded)
            
            Box(
                modifier = Modifier
                    .size(36.dp)
                    .clip(RoundedCornerShape(8.dp))
                    .background(tint.copy(alpha = 0.15f)),
                contentAlignment = Alignment.Center
            ) {
                Icon(
                    imageVector = icon,
                    contentDescription = null,
                    tint = tint,
                    modifier = Modifier.size(20.dp)
                )
            }
            Spacer(modifier = Modifier.width(16.dp))
            Text(
                text = node.name,
                style = if (node.isDir) MaterialTheme.typography.titleMedium else MaterialTheme.typography.bodyLarge,
                fontWeight = if (node.isDir) FontWeight.SemiBold else FontWeight.Normal,
                color = if (node.isDir) MaterialTheme.colorScheme.onSurface else MaterialTheme.colorScheme.onSurfaceVariant
            )
            
            if (node.isDir) {
                Spacer(modifier = Modifier.weight(1f))
                Icon(
                    imageVector = if (isExpanded) Icons.Default.KeyboardArrowDown else Icons.AutoMirrored.Filled.KeyboardArrowRight,
                    contentDescription = null,
                    tint = MaterialTheme.colorScheme.onSurfaceVariant.copy(alpha = 0.5f),
                    modifier = Modifier.size(20.dp)
                )
            }
        }
    }

    if (isTopLevel) {
        ElevatedCard(
            modifier = Modifier.fillMaxWidth(),
            colors = CardDefaults.elevatedCardColors(
                containerColor = MaterialTheme.colorScheme.surface
            ),
            elevation = CardDefaults.elevatedCardElevation(defaultElevation = 2.dp),
            shape = RoundedCornerShape(12.dp)
        ) {
            Column {
                content()
                val children = node.children
                if (node.isDir && isExpanded && children != null) {
                    HorizontalDivider(modifier = Modifier.padding(start = 56.dp), color = MaterialTheme.colorScheme.surfaceVariant.copy(alpha = 0.5f))
                    children.forEach { child ->
                        FileTreeNode(
                            node = child,
                            depth = depth + 1,
                            expandedFolders = expandedFolders,
                            onToggleFolder = onToggleFolder,
                            onOpenFile = onOpenFile
                        )
                    }
                }
            }
        }
    } else {
        Column {
            content()
            val children = node.children
            if (node.isDir && isExpanded && children != null) {
                children.forEach { child ->
                    FileTreeNode(
                        node = child,
                        depth = depth + 1,
                        expandedFolders = expandedFolders,
                        onToggleFolder = onToggleFolder,
                        onOpenFile = onOpenFile
                    )
                }
            }
        }
    }
}

@Composable
private fun getIconForNode(node: FileNode, isExpanded: Boolean): Pair<ImageVector, Color> {
    if (node.isDir) {
        return Pair(
            if (isExpanded) Icons.Default.FolderOpen else Icons.Default.Folder,
            Color(0xFF81D4FA) // Light blue for folders
        )
    }
    
    val ext = node.name.substringAfterLast('.', "")
    return when (ext.lowercase()) {
        "kt", "java" -> Pair(Icons.Default.Code, Color(0xFFC62828)) // Kotlin/Java
        "xml" -> Pair(Icons.Default.Code, Color(0xFFE65100))
        "json" -> Pair(Icons.Default.DataObject, Color(0xFF2E7D32))
        "md", "txt" -> Pair(Icons.AutoMirrored.Filled.Article, Color(0xFF4527A0))
        "png", "jpg", "jpeg", "webp" -> Pair(Icons.Default.Image, Color(0xFF00695C))
        else -> Pair(Icons.Default.Description, Color(0xFF616161))
    }
}
