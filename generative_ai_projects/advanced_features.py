"""
Advanced Features and Utilities for Facilities Management UI
This module provides additional functionality to enhance the main application
"""

import streamlit as st
from datetime import datetime, timedelta
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
from typing import List, Dict
import json


class NotificationManager:
    """Manage in-app notifications"""
    
    @staticmethod
    def add_notification(message: str, type: str = "info", duration: int = 5):
        """Add a notification to the queue"""
        if 'notifications' not in st.session_state:
            st.session_state.notifications = []
        
        notification = {
            'message': message,
            'type': type,
            'timestamp': datetime.now(),
            'duration': duration,
            'id': len(st.session_state.notifications)
        }
        st.session_state.notifications.append(notification)
    
    @staticmethod
    def display_notifications():
        """Display all active notifications"""
        if 'notifications' not in st.session_state:
            return
        
        current_time = datetime.now()
        active_notifications = []
        
        for notif in st.session_state.notifications:
            time_diff = (current_time - notif['timestamp']).seconds
            if time_diff < notif['duration']:
                active_notifications.append(notif)
                
                # Display notification
                icon_map = {
                    'success': '✅',
                    'error': '❌',
                    'warning': '⚠️',
                    'info': 'ℹ️'
                }
                
                color_map = {
                    'success': '#d4edda',
                    'error': '#f8d7da',
                    'warning': '#fff3cd',
                    'info': '#d1ecf1'
                }
                
                st.markdown(f"""
                    <div style="
                        position: fixed;
                        top: {20 + notif['id'] * 70}px;
                        right: 20px;
                        background: {color_map.get(notif['type'], color_map['info'])};
                        padding: 1rem 1.5rem;
                        border-radius: 10px;
                        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
                        z-index: 9999;
                        animation: slideIn 0.3s ease-out;
                        max-width: 400px;
                    ">
                        {icon_map.get(notif['type'], icon_map['info'])} {notif['message']}
                    </div>
                """, unsafe_allow_html=True)
        
        st.session_state.notifications = active_notifications


class AdvancedAnalytics:
    """Advanced analytics and visualization"""
    
    @staticmethod
    def create_usage_chart(messages: List[Dict]) -> go.Figure:
        """Create usage trend chart"""
        if not messages:
            return None
        
        # Group messages by date
        dates = {}
        for msg in messages:
            if 'timestamp' in msg:
                date = datetime.fromisoformat(msg['timestamp']).date()
                dates[date] = dates.get(date, 0) + 1
        
        df = pd.DataFrame(list(dates.items()), columns=['Date', 'Messages'])
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=df['Date'],
            y=df['Messages'],
            mode='lines+markers',
            fill='tozeroy',
            line=dict(color='rgb(102, 126, 234)', width=3),
            marker=dict(size=8, color='rgb(118, 75, 162)')
        ))
        
        fig.update_layout(
            title='Message Activity Over Time',
            xaxis_title='Date',
            yaxis_title='Number of Messages',
            height=400,
            hovermode='x unified',
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)'
        )
        
        return fig
    
    @staticmethod
    def create_topic_distribution(messages: List[Dict]) -> go.Figure:
        """Create topic distribution pie chart"""
        # Mock topic extraction - in real app, use NLP
        topics = {
            'Parking': 25,
            'Conference Rooms': 20,
            'IT Support': 18,
            'Gym & Wellness': 15,
            'Cafeteria': 12,
            'Security': 10
        }
        
        fig = go.Figure(data=[go.Pie(
            labels=list(topics.keys()),
            values=list(topics.values()),
            hole=0.4,
            marker=dict(colors=['#667eea', '#764ba2', '#f093fb', '#4facfe', '#00f2fe', '#43e97b'])
        )])
        
        fig.update_layout(
            title='Query Topics Distribution',
            height=400,
            showlegend=True
        )
        
        return fig
    
    @staticmethod
    def create_response_time_chart() -> go.Figure:
        """Create response time chart"""
        # Mock data
        times = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
        response_times = [1.2, 1.1, 1.3, 1.0, 1.2, 0.9, 1.1]
        
        fig = go.Figure(data=[
            go.Bar(
                x=times,
                y=response_times,
                marker=dict(
                    color=response_times,
                    colorscale='Viridis',
                    showscale=True
                )
            )
        ])
        
        fig.update_layout(
            title='Average Response Time by Day',
            xaxis_title='Day of Week',
            yaxis_title='Response Time (seconds)',
            height=400
        )
        
        return fig


class ChatExporter:
    """Export chat history in various formats"""
    
    @staticmethod
    def export_to_json(messages: List[Dict]) -> str:
        """Export chat to JSON"""
        return json.dumps({
            'export_date': datetime.now().isoformat(),
            'message_count': len(messages),
            'messages': messages
        }, indent=2)
    
    @staticmethod
    def export_to_markdown(messages: List[Dict]) -> str:
        """Export chat to Markdown"""
        markdown = f"# Chat Export\n\n"
        markdown += f"**Export Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        markdown += f"**Total Messages:** {len(messages)}\n\n---\n\n"
        
        for msg in messages:
            role = "👤 User" if msg['role'] == 'user' else "🤖 Assistant"
            timestamp = msg.get('timestamp', 'N/A')
            markdown += f"### {role}\n"
            if timestamp != 'N/A':
                markdown += f"*{timestamp}*\n\n"
            markdown += f"{msg['content']}\n\n"
            
            if 'sources' in msg and msg['sources']:
                markdown += "**Sources:**\n"
                for idx, source in enumerate(msg['sources'], 1):
                    markdown += f"{idx}. {source['title']}\n"
                markdown += "\n"
            
            markdown += "---\n\n"
        
        return markdown
    
    @staticmethod
    def export_to_html(messages: List[Dict]) -> str:
        """Export chat to HTML"""
        html = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Chat Export</title>
            <style>
                body {
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                    max-width: 900px;
                    margin: 50px auto;
                    padding: 20px;
                    background: #f5f5f5;
                }
                .header {
                    background: linear-gradient(135deg, #667eea, #764ba2);
                    color: white;
                    padding: 30px;
                    border-radius: 15px;
                    margin-bottom: 30px;
                }
                .message {
                    background: white;
                    padding: 20px;
                    border-radius: 10px;
                    margin-bottom: 20px;
                    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                }
                .user-message {
                    border-left: 4px solid #667eea;
                }
                .assistant-message {
                    border-left: 4px solid #764ba2;
                }
                .role {
                    font-weight: bold;
                    color: #667eea;
                    margin-bottom: 10px;
                }
                .timestamp {
                    color: #999;
                    font-size: 0.85em;
                    margin-bottom: 10px;
                }
                .sources {
                    background: #f8f9fa;
                    padding: 15px;
                    border-radius: 8px;
                    margin-top: 15px;
                }
            </style>
        </head>
        <body>
            <div class="header">
                <h1>🏢 Facilities Management Chat Export</h1>
                <p>Export Date: {date}</p>
                <p>Total Messages: {count}</p>
            </div>
        """.format(
            date=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            count=len(messages)
        )
        
        for msg in messages:
            role_class = 'user-message' if msg['role'] == 'user' else 'assistant-message'
            role_name = '👤 User' if msg['role'] == 'user' else '🤖 Assistant'
            timestamp = msg.get('timestamp', 'N/A')
            
            html += f"""
            <div class="message {role_class}">
                <div class="role">{role_name}</div>
                <div class="timestamp">{timestamp}</div>
                <div class="content">{msg['content']}</div>
            """
            
            if 'sources' in msg and msg['sources']:
                html += '<div class="sources"><strong>Sources:</strong><ul>'
                for source in msg['sources']:
                    html += f"<li>{source['title']}</li>"
                html += '</ul></div>'
            
            html += '</div>'
        
        html += """
        </body>
        </html>
        """
        
        return html


class SearchFilter:
    """Search and filter chat history"""
    
    @staticmethod
    def search_messages(messages: List[Dict], query: str) -> List[Dict]:
        """Search messages by content"""
        query_lower = query.lower()
        results = []
        
        for msg in messages:
            if query_lower in msg['content'].lower():
                results.append(msg)
        
        return results
    
    @staticmethod
    def filter_by_date(messages: List[Dict], start_date, end_date) -> List[Dict]:
        """Filter messages by date range"""
        filtered = []
        
        for msg in messages:
            if 'timestamp' in msg:
                msg_date = datetime.fromisoformat(msg['timestamp']).date()
                if start_date <= msg_date <= end_date:
                    filtered.append(msg)
        
        return filtered
    
    @staticmethod
    def filter_by_role(messages: List[Dict], role: str) -> List[Dict]:
        """Filter messages by role (user/assistant)"""
        return [msg for msg in messages if msg['role'] == role]


class KeyboardShortcuts:
    """Keyboard shortcuts handler"""
    
    @staticmethod
    def setup_shortcuts():
        """Setup keyboard shortcuts"""
        st.markdown("""
        <script>
        document.addEventListener('keydown', function(e) {
            // Ctrl/Cmd + K: Focus search
            if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
                e.preventDefault();
                document.querySelector('input[type="text"]').focus();
            }
            
            // Ctrl/Cmd + N: New chat
            if ((e.ctrlKey || e.metaKey) && e.key === 'n') {
                e.preventDefault();
                // Trigger clear chat
            }
            
            // Ctrl/Cmd + /: Toggle sidebar
            if ((e.ctrlKey || e.metaKey) && e.key === '/') {
                e.preventDefault();
                // Toggle sidebar
            }
        });
        </script>
        """, unsafe_allow_html=True)


class ThemeManager:
    """Manage UI themes"""
    
    @staticmethod
    def apply_custom_theme(theme_name: str):
        """Apply custom color theme"""
        themes = {
            'default': {
                'primary': '#667eea',
                'secondary': '#764ba2',
                'background': 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)'
            },
            'ocean': {
                'primary': '#2E86AB',
                'secondary': '#A23B72',
                'background': 'linear-gradient(135deg, #2E86AB 0%, #A23B72 100%)'
            },
            'forest': {
                'primary': '#3D5A6C',
                'secondary': '#6A994E',
                'background': 'linear-gradient(135deg, #3D5A6C 0%, #6A994E 100%)'
            },
            'sunset': {
                'primary': '#FF6B6B',
                'secondary': '#FFE66D',
                'background': 'linear-gradient(135deg, #FF6B6B 0%, #FFE66D 100%)'
            }
        }
        
        selected_theme = themes.get(theme_name, themes['default'])
        
        st.markdown(f"""
        <style>
        :root {{
            --primary-color: {selected_theme['primary']};
            --secondary-color: {selected_theme['secondary']};
            --background-gradient: {selected_theme['background']};
        }}
        </style>
        """, unsafe_allow_html=True)


class VoiceInput:
    """Voice input functionality (placeholder)"""
    
    @staticmethod
    def enable_voice_input():
        """Enable voice input (requires additional libraries)"""
        st.markdown("""
        <div style="text-align: center; padding: 20px;">
            <button style="
                width: 60px;
                height: 60px;
                border-radius: 50%;
                border: none;
                background: linear-gradient(135deg, #667eea, #764ba2);
                color: white;
                font-size: 24px;
                cursor: pointer;
                box-shadow: 0 4px 15px rgba(0,0,0,0.2);
            " onclick="startVoiceInput()">
                🎤
            </button>
            <p style="margin-top: 10px; color: #666;">Click to speak</p>
        </div>
        
        <script>
        function startVoiceInput() {
            alert('Voice input would be activated here. Requires speech recognition API.');
        }
        </script>
        """, unsafe_allow_html=True)


# Usage Examples
def demo_advanced_features():
    """Demonstration of advanced features"""
    
    st.title("🚀 Advanced Features Demo")
    
    # Notifications
    st.header("📢 Notifications")
    if st.button("Show Success Notification"):
        NotificationManager.add_notification("Operation completed successfully!", "success")
    
    if st.button("Show Error Notification"):
        NotificationManager.add_notification("An error occurred!", "error")
    
    NotificationManager.display_notifications()
    
    # Analytics
    st.header("📊 Analytics")
    if st.session_state.messages:
        chart = AdvancedAnalytics.create_usage_chart(st.session_state.messages)
        if chart:
            st.plotly_chart(chart, use_container_width=True)
        
        topic_chart = AdvancedAnalytics.create_topic_distribution(st.session_state.messages)
        st.plotly_chart(topic_chart, use_container_width=True)
    
    # Export
    st.header("💾 Export Options")
    if st.session_state.messages:
        col1, col2, col3 = st.columns(3)
        
        with col1:
            json_data = ChatExporter.export_to_json(st.session_state.messages)
            st.download_button(
                "📥 Download JSON",
                json_data,
                f"chat_{datetime.now().strftime('%Y%m%d')}.json",
                "application/json"
            )
        
        with col2:
            md_data = ChatExporter.export_to_markdown(st.session_state.messages)
            st.download_button(
                "📥 Download Markdown",
                md_data,
                f"chat_{datetime.now().strftime('%Y%m%d')}.md",
                "text/markdown"
            )
        
        with col3:
            html_data = ChatExporter.export_to_html(st.session_state.messages)
            st.download_button(
                "📥 Download HTML",
                html_data,
                f"chat_{datetime.now().strftime('%Y%m%d')}.html",
                "text/html"
            )
    
    # Search
    st.header("🔍 Search Chat History")
    search_query = st.text_input("Search messages")
    if search_query and st.session_state.messages:
        results = SearchFilter.search_messages(st.session_state.messages, search_query)
        st.write(f"Found {len(results)} results")
        for result in results:
            st.markdown(f"**{result['role']}:** {result['content'][:100]}...")
    
    # Theme Selector
    st.header("🎨 Theme Selector")
    theme = st.selectbox("Choose Theme", ["default", "ocean", "forest", "sunset"])
    ThemeManager.apply_custom_theme(theme)