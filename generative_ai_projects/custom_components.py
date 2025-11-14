"""
Custom UI Components for Enhanced User Experience
Reusable components for the Facilities Management application
"""

import streamlit as st
from datetime import datetime
from typing import List, Dict, Optional


class CustomComponents:
    """Collection of custom UI components"""
    
    @staticmethod
    def animated_header(title: str, subtitle: str = "", icon: str = "🏢"):
        """Create an animated header with gradient text"""
        st.markdown(f"""
        <div style="
            text-align: center;
            padding: 3rem 0 2rem 0;
            animation: fadeInDown 0.8s ease-out;
        ">
            <div style="font-size: 4rem; margin-bottom: 1rem;">
                {icon}
            </div>
            <h1 style="
                background: linear-gradient(135deg, #667eea, #764ba2);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                font-size: 3.5rem;
                font-weight: 800;
                margin-bottom: 0.5rem;
                animation: slideIn 1s ease-out;
            ">
                {title}
            </h1>
            <p style="
                color: #666;
                font-size: 1.3rem;
                font-weight: 400;
            ">
                {subtitle}
            </p>
        </div>
        
        <style>
        @keyframes fadeInDown {{
            from {{
                opacity: 0;
                transform: translateY(-30px);
            }}
            to {{
                opacity: 1;
                transform: translateY(0);
            }}
        }}
        
        @keyframes slideIn {{
            from {{
                opacity: 0;
                transform: translateX(-50px);
            }}
            to {{
                opacity: 1;
                transform: translateX(0);
            }}
        }}
        </style>
        """, unsafe_allow_html=True)
    
    @staticmethod
    def feature_card(icon: str, title: str, description: str, color: str = "#667eea"):
        """Create a beautiful feature card"""
        st.markdown(f"""
        <div style="
            background: white;
            padding: 2rem;
            border-radius: 16px;
            box-shadow: 0 4px 20px rgba(0,0,0,0.08);
            transition: all 0.3s ease;
            border-top: 4px solid {color};
            cursor: pointer;
        " onmouseover="this.style.transform='translateY(-8px)'; this.style.boxShadow='0 12px 30px rgba(0,0,0,0.15)';" 
           onmouseout="this.style.transform='translateY(0)'; this.style.boxShadow='0 4px 20px rgba(0,0,0,0.08)';">
            <div style="font-size: 3rem; margin-bottom: 1rem;">{icon}</div>
            <h3 style="color: #333; margin-bottom: 0.5rem; font-weight: 700;">{title}</h3>
            <p style="color: #666; line-height: 1.6; margin: 0;">{description}</p>
        </div>
        """, unsafe_allow_html=True)
    
    @staticmethod
    def progress_ring(percentage: int, label: str = "", color: str = "#667eea"):
        """Create a circular progress indicator"""
        circumference = 2 * 3.14159 * 40  # radius = 40
        offset = circumference - (percentage / 100) * circumference
        
        st.markdown(f"""
        <div style="text-align: center;">
            <svg width="120" height="120" style="transform: rotate(-90deg);">
                <circle
                    cx="60"
                    cy="60"
                    r="40"
                    stroke="#e0e0e0"
                    stroke-width="8"
                    fill="none"
                />
                <circle
                    cx="60"
                    cy="60"
                    r="40"
                    stroke="{color}"
                    stroke-width="8"
                    fill="none"
                    stroke-dasharray="{circumference}"
                    stroke-dashoffset="{offset}"
                    stroke-linecap="round"
                    style="transition: stroke-dashoffset 0.5s ease;"
                />
                <text
                    x="60"
                    y="70"
                    text-anchor="middle"
                    style="
                        font-size: 1.5rem;
                        font-weight: bold;
                        fill: {color};
                        transform: rotate(90deg);
                        transform-origin: 60px 60px;
                    "
                >
                    {percentage}%
                </text>
            </svg>
            <p style="margin-top: 0.5rem; color: #666; font-weight: 600;">{label}</p>
        </div>
        """, unsafe_allow_html=True)
    
    @staticmethod
    def timeline_item(title: str, description: str, timestamp: str, icon: str = "📌", 
                     completed: bool = False):
        """Create a timeline item"""
        status_color = "#28a745" if completed else "#667eea"
        status_icon = "✓" if completed else "○"
        
        st.markdown(f"""
        <div style="
            display: flex;
            gap: 1.5rem;
            margin-bottom: 2rem;
            position: relative;
        ">
            <div style="
                width: 40px;
                height: 40px;
                border-radius: 50%;
                background: {status_color};
                color: white;
                display: flex;
                align-items: center;
                justify-content: center;
                font-weight: bold;
                flex-shrink: 0;
                box-shadow: 0 2px 8px rgba(0,0,0,0.15);
            ">
                {icon}
            </div>
            <div style="flex: 1;">
                <div style="
                    background: white;
                    padding: 1.5rem;
                    border-radius: 12px;
                    box-shadow: 0 2px 10px rgba(0,0,0,0.08);
                    border-left: 3px solid {status_color};
                ">
                    <div style="
                        display: flex;
                        justify-content: space-between;
                        align-items: center;
                        margin-bottom: 0.5rem;
                    ">
                        <h4 style="margin: 0; color: #333;">{title}</h4>
                        <span style="
                            background: {status_color};
                            color: white;
                            padding: 0.25rem 0.75rem;
                            border-radius: 20px;
                            font-size: 0.85rem;
                            font-weight: 600;
                        ">
                            {status_icon}
                        </span>
                    </div>
                    <p style="color: #666; margin: 0.5rem 0;">{description}</p>
                    <small style="color: #999;">{timestamp}</small>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    @staticmethod
    def stat_box(value: str, label: str, icon: str, trend: str = "", color: str = "#667eea"):
        """Create an animated stat box"""
        trend_html = ""
        if trend:
            trend_color = "#28a745" if "+" in trend else "#dc3545"
            trend_html = f"""
            <span style="
                color: {trend_color};
                font-size: 0.9rem;
                font-weight: 600;
                margin-left: 0.5rem;
            ">
                {trend}
            </span>
            """
        
        st.markdown(f"""
        <div style="
            background: linear-gradient(135deg, {color}15, {color}05);
            padding: 2rem;
            border-radius: 16px;
            border: 2px solid {color}30;
            text-align: center;
            transition: all 0.3s ease;
        " onmouseover="this.style.transform='scale(1.05)'"
           onmouseout="this.style.transform='scale(1)'">
            <div style="font-size: 3rem; margin-bottom: 0.5rem;">{icon}</div>
            <div style="
                font-size: 2.5rem;
                font-weight: 800;
                color: {color};
                margin-bottom: 0.5rem;
            ">
                {value}
                {trend_html}
            </div>
            <div style="
                color: #666;
                font-size: 0.95rem;
                font-weight: 600;
                text-transform: uppercase;
                letter-spacing: 1px;
            ">
                {label}
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    @staticmethod
    def info_panel(title: str, content: str, type: str = "info"):
        """Create an information panel"""
        colors = {
            "info": {"bg": "#d1ecf1", "border": "#0c5460", "icon": "ℹ️"},
            "success": {"bg": "#d4edda", "border": "#155724", "icon": "✅"},
            "warning": {"bg": "#fff3cd", "border": "#856404", "icon": "⚠️"},
            "error": {"bg": "#f8d7da", "border": "#721c24", "icon": "❌"}
        }
        
        style = colors.get(type, colors["info"])
        
        st.markdown(f"""
        <div style="
            background: {style['bg']};
            border-left: 4px solid {style['border']};
            padding: 1.5rem;
            border-radius: 8px;
            margin: 1rem 0;
            box-shadow: 0 2px 8px rgba(0,0,0,0.08);
        ">
            <div style="display: flex; align-items: flex-start; gap: 1rem;">
                <div style="font-size: 2rem;">{style['icon']}</div>
                <div>
                    <h4 style="margin: 0 0 0.5rem 0; color: {style['border']};">{title}</h4>
                    <p style="margin: 0; color: #333; line-height: 1.6;">{content}</p>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    @staticmethod
    def tag_badge(text: str, color: str = "#667eea"):
        """Create a small badge/tag"""
        st.markdown(f"""
        <span style="
            display: inline-block;
            background: {color}20;
            color: {color};
            padding: 0.4rem 1rem;
            border-radius: 20px;
            font-size: 0.85rem;
            font-weight: 600;
            margin: 0.25rem;
            border: 2px solid {color}40;
        ">
            {text}
        </span>
        """, unsafe_allow_html=True)
    
    @staticmethod
    def loading_skeleton():
        """Create a loading skeleton animation"""
        st.markdown("""
        <div style="animation: pulse 1.5s ease-in-out infinite;">
            <div style="
                background: linear-gradient(90deg, #f0f0f0 25%, #e0e0e0 50%, #f0f0f0 75%);
                background-size: 200% 100%;
                animation: shimmer 2s infinite;
                height: 20px;
                border-radius: 4px;
                margin-bottom: 10px;
            "></div>
            <div style="
                background: linear-gradient(90deg, #f0f0f0 25%, #e0e0e0 50%, #f0f0f0 75%);
                background-size: 200% 100%;
                animation: shimmer 2s infinite;
                height: 20px;
                border-radius: 4px;
                width: 80%;
                margin-bottom: 10px;
            "></div>
            <div style="
                background: linear-gradient(90deg, #f0f0f0 25%, #e0e0e0 50%, #f0f0f0 75%);
                background-size: 200% 100%;
                animation: shimmer 2s infinite;
                height: 20px;
                border-radius: 4px;
                width: 60%;
            "></div>
        </div>
        
        <style>
        @keyframes shimmer {
            0% { background-position: -200% 0; }
            100% { background-position: 200% 0; }
        }
        
        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.5; }
        }
        </style>
        """, unsafe_allow_html=True)
    
    @staticmethod
    def tooltip(text: str, tooltip_text: str):
        """Create a text with tooltip"""
        st.markdown(f"""
        <span style="position: relative; display: inline-block;">
            <span style="
                border-bottom: 2px dotted #667eea;
                cursor: help;
            ">{text}</span>
            <span style="
                visibility: hidden;
                background-color: #333;
                color: white;
                text-align: center;
                border-radius: 6px;
                padding: 0.5rem 1rem;
                position: absolute;
                z-index: 1;
                bottom: 125%;
                left: 50%;
                margin-left: -60px;
                opacity: 0;
                transition: opacity 0.3s;
                font-size: 0.85rem;
                white-space: nowrap;
            " class="tooltip-text">
                {tooltip_text}
            </span>
        </span>
        
        <style>
        span:hover .tooltip-text {{
            visibility: visible;
            opacity: 1;
        }}
        </style>
        """, unsafe_allow_html=True)
    
    @staticmethod
    def collapsible_section(title: str, content: str, icon: str = "▼", default_open: bool = False):
        """Create a collapsible section"""
        section_id = f"section_{hash(title)}"
        display = "block" if default_open else "none"
        rotate = "rotate(0deg)" if default_open else "rotate(-90deg)"
        
        st.markdown(f"""
        <div style="margin: 1rem 0;">
            <div style="
                background: #f8f9fa;
                padding: 1rem 1.5rem;
                border-radius: 10px;
                cursor: pointer;
                display: flex;
                justify-content: space-between;
                align-items: center;
                transition: all 0.3s ease;
            " onclick="toggleSection('{section_id}')"
               onmouseover="this.style.background='#e9ecef'"
               onmouseout="this.style.background='#f8f9fa'">
                <strong style="color: #333; font-size: 1.1rem;">{title}</strong>
                <span id="icon_{section_id}" style="
                    transition: transform 0.3s ease;
                    transform: {rotate};
                ">{icon}</span>
            </div>
            <div id="{section_id}" style="
                display: {display};
                padding: 1.5rem;
                background: white;
                border-radius: 0 0 10px 10px;
                margin-top: -10px;
                border: 1px solid #e0e0e0;
                border-top: none;
            ">
                {content}
            </div>
        </div>
        
        <script>
        function toggleSection(id) {{
            var element = document.getElementById(id);
            var icon = document.getElementById('icon_' + id);
            if (element.style.display === 'none') {{
                element.style.display = 'block';
                icon.style.transform = 'rotate(0deg)';
            }} else {{
                element.style.display = 'none';
                icon.style.transform = 'rotate(-90deg)';
            }}
        }}
        </script>
        """, unsafe_allow_html=True)


# Demo function to showcase all components
def demo_custom_components():
    """Demonstration of custom components"""
    
    CustomComponents.animated_header(
        "Custom Components Library",
        "Beautiful, reusable UI elements",
        "🎨"
    )
    
    st.markdown("---")
    
    # Feature Cards
    st.subheader("Feature Cards")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        CustomComponents.feature_card(
            "🚀", "Fast Performance",
            "Lightning-fast responses powered by advanced AI",
            "#667eea"
        )
    
    with col2:
        CustomComponents.feature_card(
            "🔒", "Secure & Private",
            "Your data is encrypted and protected",
            "#764ba2"
        )
    
    with col3:
        CustomComponents.feature_card(
            "🎯", "Accurate Results",
            "Context-aware answers from your documents",
            "#f093fb"
        )
    
    st.markdown("---")
    
    # Progress Rings
    st.subheader("Progress Indicators")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        CustomComponents.progress_ring(75, "System Health", "#28a745")
    with col2:
        CustomComponents.progress_ring(92, "User Satisfaction", "#667eea")
    with col3:
        CustomComponents.progress_ring(68, "Response Rate", "#ffc107")
    with col4:
        CustomComponents.progress_ring(85, "Accuracy", "#764ba2")
    
    st.markdown("---")
    
    # Stat Boxes
    st.subheader("Statistics")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        CustomComponents.stat_box("1,234", "Total Queries", "💬", "+12%", "#667eea")
    with col2:
        CustomComponents.stat_box("98%", "Success Rate", "✅", "+2%", "#28a745")
    with col3:
        CustomComponents.stat_box("1.2s", "Avg Response", "⚡", "-0.3s", "#ffc107")
    
    st.markdown("---")
    
    # Info Panels
    st.subheader("Information Panels")
    CustomComponents.info_panel(
        "Getting Started",
        "Initialize the knowledge base to enable AI-powered responses from your documents.",
        "info"
    )
    
    CustomComponents.info_panel(
        "Success!",
        "Your document has been processed and added to the knowledge base.",
        "success"
    )
    
    # Timeline
    st.subheader("Activity Timeline")
    CustomComponents.timeline_item(
        "System Initialized",
        "RAG system successfully configured and ready",
        "2 hours ago",
        "🚀",
        True
    )
    
    CustomComponents.timeline_item(
        "Document Uploaded",
        "policy_handbook.pdf processed (45 pages)",
        "1 hour ago",
        "📄",
        True
    )
    
    CustomComponents.timeline_item(
        "Query Processed",
        "Question about parking policies answered",
        "30 minutes ago",
        "💬",
        False
    )
    
    # Tags
    st.subheader("Tags & Badges")
    CustomComponents.tag_badge("Active", "#28a745")
    CustomComponents.tag_badge("Premium", "#ffc107")
    CustomComponents.tag_badge("Verified", "#667eea")
    CustomComponents.tag_badge("Beta", "#f093fb")
    
    # Collapsible Sections
    st.subheader("Collapsible Sections")
    CustomComponents.collapsible_section(
        "FAQ: How do I use this system?",
        "Simply upload your documents and start asking questions. The AI will provide accurate answers based on your content.",
        "▼"
    )


if __name__ == "__main__":
    demo_custom_components()