#!/usr/bin/env python3
"""
GCP Context Switcher - 빠른 GCP 계정/프로젝트/GKE 클러스터 전환 도구

사용법:
    gcp-switcher          # 대화형 모드
    gcp-switcher account  # 계정만 선택
    gcp-switcher project  # 프로젝트만 선택
    gcp-switcher cluster  # GKE 클러스터 선택 및 크레덴셜 획득
    gcp-switcher context  # kubectl 컨텍스트 전환
    gcp-switcher full     # 전체 플로우 (계정 → 프로젝트 → 클러스터)
"""

import subprocess
import sys
import json
import os
import tty
import termios
import re
from typing import Optional, List, Dict, Tuple
from dataclasses import dataclass

# 색상 코드
class Colors:
    # 기본 색상
    BLACK = '\033[30m'
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    
    # 밝은 색상
    BRIGHT_BLACK = '\033[90m'
    BRIGHT_RED = '\033[91m'
    BRIGHT_GREEN = '\033[92m'
    BRIGHT_YELLOW = '\033[93m'
    BRIGHT_BLUE = '\033[94m'
    BRIGHT_MAGENTA = '\033[95m'
    BRIGHT_CYAN = '\033[96m'
    BRIGHT_WHITE = '\033[97m'
    
    # 스타일
    BOLD = '\033[1m'
    DIM = '\033[2m'
    ITALIC = '\033[3m'
    UNDERLINE = '\033[4m'
    RESET = '\033[0m'
    
    # 배경색
    BG_BLACK = '\033[40m'
    BG_RED = '\033[41m'
    BG_GREEN = '\033[42m'
    BG_YELLOW = '\033[43m'
    BG_BLUE = '\033[44m'
    BG_MAGENTA = '\033[45m'
    BG_CYAN = '\033[46m'
    BG_WHITE = '\033[47m'

def color(text: str, *colors: str) -> str:
    return ''.join(colors) + text + Colors.RESET

def clear_screen():
    print('\033[2J\033[H', end='')

def hide_cursor():
    print('\033[?25l', end='')

def show_cursor():
    print('\033[?25h', end='')

def get_terminal_size() -> Tuple[int, int]:
    try:
        size = os.get_terminal_size()
        return size.lines, size.columns
    except:
        return 24, 80

def visible_len(s: str) -> int:
    """ANSI 코드 제외한 실제 보이는 문자열 길이"""
    return len(re.sub(r'\033\[[0-9;]*m', '', s))

# ═══════════════════════════════════════════════════════════════
# ASCII 아트 및 UI 컴포넌트
# ═══════════════════════════════════════════════════════════════

LOGO = f"""
   {Colors.BRIGHT_CYAN}┌──────────────────────────────────────────────────┐{Colors.RESET}
   {Colors.BRIGHT_CYAN}│{Colors.RESET}                                                  {Colors.BRIGHT_CYAN}│{Colors.RESET}
   {Colors.BRIGHT_CYAN}│{Colors.RESET}  {Colors.BRIGHT_MAGENTA} ██████  {Colors.BRIGHT_CYAN} ██████ {Colors.BRIGHT_YELLOW} ██████ {Colors.BRIGHT_WHITE}  ██████ ███████{Colors.RESET} {Colors.BRIGHT_CYAN}│{Colors.RESET}
   {Colors.BRIGHT_CYAN}│{Colors.RESET}  {Colors.BRIGHT_MAGENTA}██       {Colors.BRIGHT_CYAN}██      {Colors.BRIGHT_YELLOW}██    ██{Colors.BRIGHT_WHITE} ██      ██     {Colors.RESET} {Colors.BRIGHT_CYAN}│{Colors.RESET}
   {Colors.BRIGHT_CYAN}│{Colors.RESET}  {Colors.BRIGHT_MAGENTA}██   ███ {Colors.BRIGHT_CYAN}██      {Colors.BRIGHT_YELLOW}██████ {Colors.BRIGHT_WHITE}  ██     ███████{Colors.RESET} {Colors.BRIGHT_CYAN}│{Colors.RESET}
   {Colors.BRIGHT_CYAN}│{Colors.RESET}  {Colors.BRIGHT_MAGENTA}██    ██ {Colors.BRIGHT_CYAN}██      {Colors.BRIGHT_YELLOW}██     {Colors.BRIGHT_WHITE}  ██          ██{Colors.RESET} {Colors.BRIGHT_CYAN}│{Colors.RESET}
   {Colors.BRIGHT_CYAN}│{Colors.RESET}  {Colors.BRIGHT_MAGENTA} ██████  {Colors.BRIGHT_CYAN} ██████ {Colors.BRIGHT_YELLOW}██     {Colors.BRIGHT_WHITE}  ██████ ███████{Colors.RESET} {Colors.BRIGHT_CYAN}│{Colors.RESET}
   {Colors.BRIGHT_CYAN}│{Colors.RESET}                                                  {Colors.BRIGHT_CYAN}│{Colors.RESET}
   {Colors.BRIGHT_CYAN}│{Colors.RESET}           {Colors.DIM}C o n t e x t   S w i t c h e r{Colors.RESET}         {Colors.BRIGHT_CYAN}│{Colors.RESET}
   {Colors.BRIGHT_CYAN}└──────────────────────────────────────────────────┘{Colors.RESET}
"""

LOGO_SMALL = f"""
   {Colors.BRIGHT_MAGENTA}GCP{Colors.RESET} {Colors.BRIGHT_WHITE}CS{Colors.RESET} {Colors.DIM}|{Colors.RESET} {Colors.BRIGHT_YELLOW}Context Switcher{Colors.RESET} {Colors.BRIGHT_GREEN}v1.0{Colors.RESET}
"""

def draw_box(title: str, content: List[str], width: int = 55, style: str = "rounded") -> str:
    """박스 그리기"""
    if style == "rounded":
        tl, tr, bl, br, h, v = "╭", "╮", "╰", "╯", "─", "│"
    elif style == "double":
        tl, tr, bl, br, h, v = "╔", "╗", "╚", "╝", "═", "║"
    else:
        tl, tr, bl, br, h, v = "┌", "┐", "└", "┘", "─", "│"
    
    box_color = Colors.BRIGHT_CYAN
    title_color = Colors.BRIGHT_YELLOW + Colors.BOLD
    
    lines = []
    
    # 상단
    if title:
        title_display = f" {title} "
        padding = width - len(title) - 4
        lines.append(f"   {box_color}{tl}{h}{title_color}{title_display}{Colors.RESET}{box_color}{h * padding}{tr}{Colors.RESET}")
    else:
        lines.append(f"   {box_color}{tl}{h * (width - 2)}{tr}{Colors.RESET}")
    
    # 내용
    for line in content:
        vis_len = visible_len(line)
        padding = width - vis_len - 4
        padding = max(0, padding)
        lines.append(f"   {box_color}{v}{Colors.RESET}  {line}{' ' * padding}{box_color}{v}{Colors.RESET}")
    
    # 하단
    lines.append(f"   {box_color}{bl}{h * (width - 2)}{br}{Colors.RESET}")
    
    return '\n'.join(lines)

def draw_status_bar(account: str, project: str, context: str) -> str:
    """상태 바 그리기"""
    rows, cols = get_terminal_size()
    width = min(cols - 4, 55)
    
    acc_icon = f"{Colors.BRIGHT_GREEN}●{Colors.RESET}" if account else f"{Colors.RED}○{Colors.RESET}"
    prj_icon = f"{Colors.BRIGHT_GREEN}●{Colors.RESET}" if project else f"{Colors.RED}○{Colors.RESET}"
    ctx_icon = f"{Colors.BRIGHT_GREEN}●{Colors.RESET}" if context else f"{Colors.RED}○{Colors.RESET}"
    
    # 긴 값 자르기
    max_val_len = width - 18
    acc_display = (account[:max_val_len-2] + "..") if account and len(account) > max_val_len else (account or "(none)")
    prj_display = (project[:max_val_len-2] + "..") if project and len(project) > max_val_len else (project or "(none)")
    ctx_display = (context[:max_val_len-2] + "..") if context and len(context) > max_val_len else (context or "(none)")
    
    content = [
        f"{acc_icon} {Colors.DIM}Account:{Colors.RESET}  {Colors.BRIGHT_WHITE}{acc_display}{Colors.RESET}",
        f"{prj_icon} {Colors.DIM}Project:{Colors.RESET}  {Colors.BRIGHT_WHITE}{prj_display}{Colors.RESET}",
        f"{ctx_icon} {Colors.DIM}Context:{Colors.RESET}  {Colors.BRIGHT_WHITE}{ctx_display}{Colors.RESET}",
    ]
    
    return draw_box("📊 Current Status", content, width)

def print_success(text: str):
    print(f"   {Colors.BRIGHT_GREEN}✔{Colors.RESET} {text}")

def print_error(text: str):
    print(f"   {Colors.BRIGHT_RED}✖{Colors.RESET} {text}")

def print_info(text: str):
    print(f"   {Colors.BRIGHT_BLUE}ℹ{Colors.RESET} {text}")

def print_warning(text: str):
    print(f"   {Colors.BRIGHT_YELLOW}⚠{Colors.RESET} {text}")

def print_spinner(text: str):
    print(f"   {Colors.BRIGHT_CYAN}◐{Colors.RESET} {text}")

def run_command(cmd: List[str], capture: bool = True, check: bool = True) -> Optional[str]:
    """명령어 실행"""
    try:
        if capture:
            result = subprocess.run(cmd, capture_output=True, text=True, check=check)
            return result.stdout.strip()
        else:
            subprocess.run(cmd, check=check)
            return None
    except subprocess.CalledProcessError as e:
        if capture:
            return None
        raise
    except FileNotFoundError:
        print_error(f"Command not found: {cmd[0]}")
        return None


class InteractiveSelector:
    """화살표 키로 선택하는 인터랙티브 셀렉터 (검색 기능 포함)"""
    
    def __init__(self, items: List[str], prompt: str, current_marker: str = None, icon: str = "", header: str = ""):
        self.original_items = items
        self.items = items
        self.prompt = prompt
        self.current_marker = current_marker
        self.icon = icon
        self.header = header
        self.selected_index = 0
        self.scroll_offset = 0
        self.search_mode = False
        self.search_query = ""
        
        # 현재 항목이 있으면 그 위치에서 시작
        if current_marker:
            for i, item in enumerate(items):
                if current_marker in item or item == current_marker:
                    self.selected_index = i
                    break
    
    def _filter_items(self):
        """검색어로 항목 필터링"""
        if not self.search_query:
            self.items = self.original_items
        else:
            query = self.search_query.lower()
            self.items = [item for item in self.original_items if query in item.lower()]
        
        self.selected_index = min(self.selected_index, max(0, len(self.items) - 1))
        self.scroll_offset = 0
    
    def _get_key(self) -> str:
        """키 입력 읽기"""
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setraw(fd)
            ch = sys.stdin.read(1)
            
            if ch == '\x1b':
                ch2 = sys.stdin.read(1)
                if ch2 == '[':
                    ch3 = sys.stdin.read(1)
                    if ch3 == 'A':
                        return 'UP'
                    elif ch3 == 'B':
                        return 'DOWN'
                    elif ch3 == 'C':
                        return 'RIGHT'
                    elif ch3 == 'D':
                        return 'LEFT'
                return 'ESC'
            elif ch == '\r' or ch == '\n':
                return 'ENTER'
            elif ch == '\x7f' or ch == '\x08':
                return 'BACKSPACE'
            elif ch == '\x03':
                return 'QUIT'
            elif ch == '/':
                return 'SEARCH'
            
            if not self.search_mode:
                if ch == 'q' or ch == 'Q':
                    return 'QUIT'
                elif ch == 'j':
                    return 'DOWN'
                elif ch == 'k':
                    return 'UP'
            
            return ch
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
    
    def _render(self):
        """화면 렌더링"""
        rows, cols = get_terminal_size()
        max_visible = min(len(self.items), rows - 16)
        max_visible = max(max_visible, 3)
        
        if self.selected_index < self.scroll_offset:
            self.scroll_offset = self.selected_index
        elif self.selected_index >= self.scroll_offset + max_visible:
            self.scroll_offset = self.selected_index - max_visible + 1
        
        # 헤더 출력 (있는 경우)
        if self.header:
            print(self.header)
        
        # 프롬프트 (박스 형태)
        print(f"   {Colors.BRIGHT_CYAN}╭─{Colors.RESET} {self.icon} {Colors.BOLD}{self.prompt}{Colors.RESET}")
        print(f"   {Colors.BRIGHT_CYAN}│{Colors.RESET}")
        
        # 검색창
        if self.search_mode:
            print(f"   {Colors.BRIGHT_CYAN}│{Colors.RESET}  {Colors.BG_YELLOW}{Colors.BLACK} 🔍 SEARCH {Colors.RESET} {self.search_query}{Colors.BRIGHT_YELLOW}▌{Colors.RESET}")
            print(f"   {Colors.BRIGHT_CYAN}│{Colors.RESET}")
        elif self.search_query:
            count_info = f"({len(self.items)}/{len(self.original_items)})"
            print(f"   {Colors.BRIGHT_CYAN}│{Colors.RESET}  {Colors.DIM}🔍 Filter: {self.search_query} {count_info}{Colors.RESET}")
            print(f"   {Colors.BRIGHT_CYAN}│{Colors.RESET}")
        
        # 항목 출력
        if not self.items:
            print(f"   {Colors.BRIGHT_CYAN}│{Colors.RESET}  {Colors.DIM}No results found.{Colors.RESET}")
        else:
            visible_items = self.items[self.scroll_offset:self.scroll_offset + max_visible]
            
            # 스크롤 위 표시
            if self.scroll_offset > 0:
                print(f"   {Colors.BRIGHT_CYAN}│{Colors.RESET}     {Colors.DIM}↑ {self.scroll_offset} more{Colors.RESET}")
            
            for i, item in enumerate(visible_items):
                actual_index = i + self.scroll_offset
                
                is_current = self.current_marker and (self.current_marker in item or item == self.current_marker)
                
                if actual_index == self.selected_index:
                    # 선택된 항목 - 하이라이트 배경
                    print(f"   {Colors.BRIGHT_CYAN}│{Colors.RESET}  {Colors.BG_CYAN}{Colors.BLACK} ▸ {item} {Colors.RESET}", end='')
                    if is_current:
                        print(f" {Colors.BG_GREEN}{Colors.BLACK} ✓ {Colors.RESET}")
                    else:
                        print()
                else:
                    # 일반 항목
                    display = item
                    # 검색어 하이라이트
                    if self.search_query:
                        query = self.search_query.lower()
                        idx = item.lower().find(query)
                        if idx != -1:
                            before = item[:idx]
                            match = item[idx:idx+len(self.search_query)]
                            after = item[idx+len(self.search_query):]
                            display = f"{Colors.DIM}{before}{Colors.RESET}{Colors.BRIGHT_YELLOW}{Colors.BOLD}{match}{Colors.RESET}{Colors.DIM}{after}{Colors.RESET}"
                        else:
                            display = f"{Colors.DIM}{item}{Colors.RESET}"
                    else:
                        display = f"{Colors.DIM}{item}{Colors.RESET}"
                    
                    print(f"   {Colors.BRIGHT_CYAN}│{Colors.RESET}    {display}", end='')
                    if is_current:
                        print(f" {Colors.BRIGHT_GREEN}✓{Colors.RESET}")
                    else:
                        print()
            
            # 스크롤 아래 표시
            remaining = len(self.items) - (self.scroll_offset + max_visible)
            if remaining > 0:
                print(f"   {Colors.BRIGHT_CYAN}│{Colors.RESET}     {Colors.DIM}↓ {remaining} more{Colors.RESET}")
        
        print(f"   {Colors.BRIGHT_CYAN}│{Colors.RESET}")
        
        # 도움말 (하단 박스)
        if self.search_mode:
            print(f"   {Colors.BRIGHT_CYAN}╰─{Colors.RESET} {Colors.DIM}Enter{Colors.RESET} done  {Colors.DIM}ESC{Colors.RESET} cancel")
        else:
            print(f"   {Colors.BRIGHT_CYAN}╰─{Colors.RESET} {Colors.DIM}↑↓{Colors.RESET} move  {Colors.DIM}/{Colors.RESET} search  {Colors.DIM}Enter{Colors.RESET} select  {Colors.DIM}q{Colors.RESET} quit")
    
    def select(self) -> Optional[str]:
        """선택 UI 실행"""
        if not self.items:
            print_warning("No items to select.")
            return None
        
        try:
            hide_cursor()
            
            while True:
                clear_screen()
                self._render()
                
                key = self._get_key()
                
                if self.search_mode:
                    if key == 'ENTER':
                        self.search_mode = False
                    elif key == 'ESC':
                        self.search_mode = False
                        self.search_query = ""
                        self._filter_items()
                    elif key == 'BACKSPACE':
                        if self.search_query:
                            self.search_query = self.search_query[:-1]
                            self._filter_items()
                    elif len(key) == 1 and key.isprintable():
                        self.search_query += key
                        self._filter_items()
                else:
                    if key == 'UP':
                        self.selected_index = max(0, self.selected_index - 1)
                    elif key == 'DOWN':
                        self.selected_index = min(len(self.items) - 1, self.selected_index + 1) if self.items else 0
                    elif key == 'ENTER':
                        if self.items:
                            show_cursor()
                            clear_screen()
                            return self.items[self.selected_index]
                    elif key == 'SEARCH':
                        self.search_mode = True
                    elif key in ('QUIT', 'ESC'):
                        if self.search_query:
                            self.search_query = ""
                            self._filter_items()
                        else:
                            show_cursor()
                            clear_screen()
                            return None
                    
        except Exception as e:
            show_cursor()
            raise
        finally:
            show_cursor()


class GCPSwitcher:
    def __init__(self):
        self.current_account: Optional[str] = None
        self.current_project: Optional[str] = None
        self.current_cluster: Optional[str] = None
        self.current_context: Optional[str] = None
        self._load_current_state()
    
    def _load_current_state(self):
        """현재 설정된 상태 로드"""
        self.current_account = run_command(['gcloud', 'config', 'get-value', 'account'])
        self.current_project = run_command(['gcloud', 'config', 'get-value', 'project'])
        self.current_context = run_command(['kubectl', 'config', 'current-context'], check=False)
    
    def print_status(self):
        """현재 상태 출력"""
        print(draw_status_bar(self.current_account, self.current_project, self.current_context))
    
    def get_accounts(self) -> List[str]:
        """인증된 계정 목록"""
        output = run_command(['gcloud', 'auth', 'list', '--format=value(account)'])
        if output:
            return [acc.strip() for acc in output.split('\n') if acc.strip()]
        return []
    
    def get_projects(self) -> List[str]:
        """접근 가능한 프로젝트 목록"""
        print_spinner("Fetching projects...")
        output = run_command(['gcloud', 'projects', 'list', '--format=value(projectId)'])
        if output:
            projects = [p.strip() for p in output.split('\n') if p.strip()]
            return sorted(projects)
        return []
    
    def get_clusters(self) -> List[Dict]:
        """GKE 클러스터 목록"""
        print_spinner("Fetching GKE clusters...")
        output = run_command([
            'gcloud', 'container', 'clusters', 'list',
            '--format=json'
        ])
        if output:
            try:
                clusters = json.loads(output)
                return clusters
            except json.JSONDecodeError:
                return []
        return []
    
    def get_kubectl_contexts(self) -> List[str]:
        """kubectl 컨텍스트 목록"""
        output = run_command(['kubectl', 'config', 'get-contexts', '-o=name'])
        if output:
            return [ctx.strip() for ctx in output.split('\n') if ctx.strip()]
        return []
    
    def switch_account(self, account: str) -> bool:
        """계정 전환"""
        print_spinner(f"Switching account to {account}...")
        result = run_command(['gcloud', 'config', 'set', 'account', account])
        if result is not None or result == '':
            self.current_account = account
            print_success(f"Account switched to {Colors.BRIGHT_CYAN}{account}{Colors.RESET}")
            return True
        print_error("Failed to switch account")
        return False
    
    def switch_project(self, project: str) -> bool:
        """프로젝트 전환"""
        print_spinner(f"Switching project to {project}...")
        result = run_command(['gcloud', 'config', 'set', 'project', project])
        if result is not None or result == '':
            self.current_project = project
            print_success(f"Project switched to {Colors.BRIGHT_CYAN}{project}{Colors.RESET}")
            return True
        print_error("Failed to switch project")
        return False
    
    def get_cluster_credentials(self, cluster_name: str, zone: str, regional: bool = False) -> bool:
        """GKE 클러스터 크레덴셜 획득"""
        print_spinner(f"Fetching credentials for {cluster_name}...")
        
        location_flag = '--region' if regional else '--zone'
        cmd = [
            'gcloud', 'container', 'clusters', 'get-credentials',
            cluster_name, location_flag, zone
        ]
        
        try:
            run_command(cmd, capture=False)
            self.current_cluster = cluster_name
            self._load_current_state()
            print_success(f"Credentials fetched for {Colors.BRIGHT_CYAN}{cluster_name}{Colors.RESET}")
            print_success(f"Context: {Colors.BRIGHT_CYAN}{self.current_context or '(unknown)'}{Colors.RESET}")
            return True
        except subprocess.CalledProcessError:
            print_error("Failed to fetch credentials")
            return False
    
    def switch_kubectl_context(self, context: str) -> bool:
        """kubectl 컨텍스트 전환"""
        print_spinner(f"Switching context to {context}...")
        try:
            run_command(['kubectl', 'config', 'use-context', context], capture=False)
            self.current_context = context
            print_success(f"Context switched to {Colors.BRIGHT_CYAN}{context}{Colors.RESET}")
            return True
        except subprocess.CalledProcessError:
            print_error("Failed to switch context")
            return False
    
    def auth_login(self) -> bool:
        """새 계정으로 인증"""
        print_info("Opening browser for authentication...")
        try:
            run_command(['gcloud', 'auth', 'login'], capture=False)
            self._load_current_state()
            print_success("Login successful!")
            return True
        except subprocess.CalledProcessError:
            print_error("Login failed")
            return False
    
    # ============ 대화형 메뉴 ============
    
    def menu_select_account(self) -> Optional[str]:
        """계정 선택 메뉴"""
        accounts = self.get_accounts()
        accounts.append(f"➕ Login with new account")
        
        selector = InteractiveSelector(
            accounts, 
            "Select Account",
            self.current_account,
            "🔑"
        )
        choice = selector.select()
        
        if choice is None:
            return None
        
        if 'Login with new account' in choice:
            self.auth_login()
            return self.current_account
        
        if choice != self.current_account:
            self.switch_account(choice)
        return choice
    
    def menu_select_project(self) -> Optional[str]:
        """프로젝트 선택 메뉴"""
        projects = self.get_projects()
        
        if not projects:
            print_warning("No accessible projects found.")
            return None
        
        selector = InteractiveSelector(
            projects,
            "Select Project",
            self.current_project,
            "📁"
        )
        choice = selector.select()
        
        if choice is None:
            return None
        
        if choice != self.current_project:
            self.switch_project(choice)
        return choice
    
    def menu_select_cluster(self) -> Optional[str]:
        """GKE 클러스터 선택 및 크레덴셜 획득"""
        clusters = self.get_clusters()
        
        if not clusters:
            print_warning("No GKE clusters found in this project.")
            # 기존 context 해제
            self.clear_kubectl_context()
            return None
        
        display_clusters = []
        cluster_info = {}
        
        for c in clusters:
            name = c.get('name', 'unknown')
            location = c.get('zone', c.get('location', 'unknown'))
            status = c.get('status', 'unknown')
            
            is_regional = '-' not in location.split('-')[-1] or len(location.split('-')[-1]) > 1
            
            status_icon = "🟢" if status == "RUNNING" else "🟡" if status == "PROVISIONING" else "🔴"
            display = f"{status_icon} {name} ({location})"
            display_clusters.append(display)
            cluster_info[display] = {
                'name': name,
                'location': location,
                'regional': is_regional
            }
        
        selector = InteractiveSelector(
            display_clusters,
            "Select GKE Cluster",
            None,
            "☸️"
        )
        choice = selector.select()
        
        if choice is None:
            return None
        
        info = cluster_info[choice]
        self.get_cluster_credentials(info['name'], info['location'], info['regional'])
        return info['name']
    
    def clear_kubectl_context(self):
        """kubectl context 해제"""
        try:
            run_command(['kubectl', 'config', 'unset', 'current-context'], capture=False)
            self.current_context = None
            print_warning("kubectl context has been cleared.")
        except subprocess.CalledProcessError:
            pass
    
    def menu_select_context(self) -> Optional[str]:
        """kubectl 컨텍스트 선택"""
        contexts = self.get_kubectl_contexts()
        
        if not contexts:
            print_warning("No kubectl contexts found.")
            return None
        
        selector = InteractiveSelector(
            contexts,
            "Select kubectl Context",
            self.current_context,
            "🔄"
        )
        choice = selector.select()
        
        if choice is None:
            return None
        
        if choice != self.current_context:
            self.switch_kubectl_context(choice)
        return choice
    
    def menu_full_flow(self):
        """전체 플로우: 계정 → 프로젝트 → 클러스터"""
        result = self.menu_select_account()
        if result is None:
            return
        
        result = self.menu_select_project()
        if result is None:
            return
        
        self.menu_select_cluster()
        
        print()
        self.print_status()
        print()
        print_success("Configuration complete! 🎉")
        input(f"\n   {Colors.DIM}Press Enter to continue...{Colors.RESET}")
    
    def main_menu(self):
        """메인 메뉴"""
        options = [
            "🔑  Switch Account",
            "📁  Switch Project",
            "☸️   Connect to GKE Cluster",
            "🔄  Switch kubectl Context",
            "🚀  Full Setup (Account → Project → Cluster)",
        ]
        
        while True:
            self._load_current_state()
            
            # 로고 + 상태바를 프롬프트에 포함
            header = f"""{LOGO}
{draw_status_bar(self.current_account, self.current_project, self.current_context)}
"""
            
            selector = InteractiveSelector(options, "Select Action", None, "⚡", header=header)
            choice = selector.select()
            
            if choice is None:
                clear_screen()
                print(f"\n   {Colors.BRIGHT_CYAN}👋 Goodbye!{Colors.RESET}\n")
                break
            
            if "Account" in choice:
                self.menu_select_account()
            elif "Project" in choice:
                self.menu_select_project()
            elif "GKE" in choice:
                self.menu_select_cluster()
            elif "kubectl" in choice:
                self.menu_select_context()
            elif "Full" in choice:
                self.menu_full_flow()


def main():
    if not run_command(['which', 'gcloud']):
        print_error("gcloud CLI is not installed.")
        print_info("Install from: https://cloud.google.com/sdk/docs/install")
        sys.exit(1)
    
    switcher = GCPSwitcher()
    
    if len(sys.argv) > 1:
        cmd = sys.argv[1].lower()
        
        if cmd == 'account':
            switcher.menu_select_account()
        elif cmd == 'project':
            switcher.menu_select_project()
        elif cmd == 'cluster':
            switcher.menu_select_cluster()
        elif cmd == 'context':
            switcher.menu_select_context()
        elif cmd == 'full':
            switcher.menu_full_flow()
        elif cmd == 'status':
            print(LOGO_SMALL)
            switcher.print_status()
        elif cmd in ['help', '-h', '--help']:
            print(LOGO_SMALL)
            print(__doc__)
        else:
            print_warning(f"Unknown command: {cmd}")
            print(__doc__)
    else:
        try:
            switcher.main_menu()
        except KeyboardInterrupt:
            show_cursor()
            print(f"\n\n   {Colors.BRIGHT_CYAN}👋 Goodbye!{Colors.RESET}\n")

if __name__ == '__main__':
    main()
