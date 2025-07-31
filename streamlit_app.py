import streamlit as st
import time
from datetime import datetime
from workflow import create_research_workflow
from langchain_core.messages import HumanMessage
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.colors import HexColor
import io

# Page config
st.set_page_config(
    page_title="� ESG Research & Reporting System",
    page_icon="�",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .agent-card {
        padding: 1rem;
        border-radius: 10px;
        margin: 1rem 0;
        border-left: 4px solid;
    }
    .lead-agent { border-left-color: #ff6b6b; background-color: #fff5f5; }
    .academic-agent { border-left-color: #4ecdc4; background-color: #f0fffe; }
    .web-agent { border-left-color: #45b7d1; background-color: #f0f9ff; }
    .data-agent { border-left-color: #96ceb4; background-color: #f0fff4; }
    .verification-agent { border-left-color: #ffeaa7; background-color: #fffdf0; }
    .synthesis-agent { border-left-color: #fd79a8; background-color: #fef7f0; }
    
    .status-running { color: #ff6b6b; }
    .status-complete { color: #00b894; }
    .status-waiting { color: #636e72; }
    
    .agent-avatar {
        font-size: 4rem;
        text-align: center;
        margin: 0.5rem;
        animation: bounce 2s infinite;
    }
    
    .agent-avatar.active {
        animation: colorPulse 1.2s infinite ease-in-out;
    }
    
    .agent-avatar.complete {
        animation: none;
        opacity: 0.7;
    }
    
    @keyframes bounce {
        0%, 20%, 50%, 80%, 100% { transform: translateY(0); }
        40% { transform: translateY(-10px); }
        60% { transform: translateY(-5px); }
    }
    
    @keyframes colorPulse {
        0% { 
            filter: brightness(1) hue-rotate(0deg) saturate(1);
            transform: scale(1);
            text-shadow: 0 0 10px rgba(255, 107, 107, 0.3);
        }
        50% { 
            filter: brightness(1.4) hue-rotate(45deg) saturate(1.5);
            transform: scale(1);
            text-shadow: 0 0 20px rgba(255, 107, 107, 0.8);
        }
        100% { 
            filter: brightness(1) hue-rotate(0deg) saturate(1);
            transform: scale(1);
            text-shadow: 0 0 10px rgba(255, 107, 107, 0.3);
        }
    }
    
    .workflow-stage {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 1rem;
        border-radius: 10px;
        margin: 1rem 0;
        text-align: center;
    }
    
    .agent-instruction {
        background: #f8f9fa;
        border: 2px dashed #dee2e6;
        border-radius: 8px;
        padding: 0.5rem;
        margin: 0.5rem 0;
        font-style: italic;
        animation: fadeIn 0.5s ease-in;
    }
    
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(10px); }
        to { opacity: 1; transform: translateY(0); }
    }
    
    .agent-handoff {
        display: flex;
        align-items: center;
        justify-content: center;
        margin: 1rem 0;
        font-size: 1.5rem;
    }
    
    .mission-control {
        background: linear-gradient(135deg, #2d3748 0%, #4a5568 100%);
        color: white;
        padding: 1rem;
        border-radius: 10px;
        margin: 1rem 0;
        max-height: 400px;
        overflow-y: auto;
    }
    
    .mission-event {
        background: rgba(255, 255, 255, 0.1);
        padding: 0.5rem;
        margin: 0.25rem 0;
        border-radius: 5px;
        border-left: 3px solid #4fd1c7;
        font-size: 0.9rem;
    }
</style>""", unsafe_allow_html=True)

def get_agent_emoji(agent_name):
    """Get fun emojis for each agent"""
    emojis = {
        "lead_agent": "🎯",
        "academic_search": "🎓",
        "web_search": "🌐", 
        "data_search": "�",
        "aggregator": "⚡",
        "verification_agent": "📝",
        "synthesis": "🧠"
    }
    return emojis.get(agent_name, "🤖")

def get_agent_personality(agent_name):
    """Get fun personality descriptions for each agent"""
    personalities = {
        "lead_agent": "The Master Orchestrator 🎯\n*Conducting the research symphony*",
        "academic_search": "The Scholar 🎓\n*Diving deep into research papers*",
        "web_search": "The News Hound 🌐\n*Sniffing out the latest intel*",
        "data_search": "The ESG Specialist �\n*Unlocking sustainability insights*",
        "aggregator": "The Collector ⚡\n*Gathering all the evidence*",
        "verification_agent": "The Fact Checker 📝\n*Ensuring everything is legit*",
        "synthesis": "The Mastermind 🧠\n*Weaving it all together*"
    }
    return personalities.get(agent_name, "The Mystery Agent 🤖")


def get_agent_avatar(agent_name, status="waiting"):
    """Get animated avatar for each agent based on status"""
    avatars = {
        "lead_agent": "🎭",
        "academic_search": "🎓", 
        "web_search": "🌐",
        "data_search": "�",
        "aggregator": "🔄",
        "verification_agent": "📋",
        "synthesis": "🧠"
    }
    
    emoji = avatars.get(agent_name, "🤖")
    css_class = f"agent-avatar {status}"
    
    return f'<div class="{css_class}">{emoji}</div>'

def get_funny_instruction(from_agent, to_agent):
    """Get funny instructions between agents"""
    instructions = {
        ("lead_agent", "academic_search"): "🎯➡️🎓 'Hey Scholar! Go dig up some brainy papers!'",
        ("lead_agent", "web_search"): "🎯➡️🌐 'News Hound! Sniff out the latest intel!'", 
        ("lead_agent", "data_search"): "🎯➡️� 'ESG Specialist! Unlock those sustainability insights!'",
        ("aggregator", "verification_agent"): "🔄➡️📋 'Fact Checker! Make sure everything checks out!'",
        ("verification_agent", "synthesis"): "📋➡️🧠 'Mastermind! Work your magic and tie it all together!'"
    }
    
    return instructions.get((from_agent, to_agent), f"🤝 {from_agent} ➡️ {to_agent}")
def update_mission_control_sidebar():
    """Update the mission control display in the sidebar"""
    if 'mission_control_placeholder' in st.session_state and st.session_state.mission_control_placeholder:
        # Ensure mission_events is initialized
        if 'mission_events' not in st.session_state:
            st.session_state.mission_events = []
            
        with st.session_state.mission_control_placeholder.container():
            if st.session_state.mission_events:
                st.markdown("### 📜 Mission Log")
                for event in st.session_state.mission_events[-8:]:  # Show last 8 events
                    st.markdown(f"- {event}")
            else:
                st.info("🎬 Awaiting mission deployment...")
                st.markdown("*Mission updates will appear here during agent execution*")

def get_agent_completed_work(agent_name):
    """Get the completed work content for a specific agent from session state"""
    # Try to get from session state
    agent_work_key = f"agent_work_{agent_name}"
    if agent_work_key in st.session_state:
        return st.session_state[agent_work_key]
    
    # Fallback descriptions if no specific content available
    fallback_descriptions = {
        "lead_agent": "Analyzed the research query and coordinated the multi-agent workflow. Broke down the complex ESG research question into specific subtasks for specialized agents.",
        "academic_search": "Searched academic databases and research papers for relevant ESG literature. Found scholarly articles and studies related to the query.",
        "web_search": "Gathered current market intelligence and recent news related to ESG developments. Collected real-time information to complement academic sources.",
        "data_search": "Accessed the indexed ESG document repository via Azure AI Search. Retrieved relevant sustainability reports, ESG frameworks, and regulatory documents.",
        "aggregator": "Compiled and organized all research findings from the specialized search agents. Structured the information for quality control and synthesis.",
        "verification_agent": "Verified all sources and ensured proper attribution for academic papers, ESG reports, and market data. Maintained research integrity standards.",
        "synthesis": "Integrated all research findings into a comprehensive ESG analysis. Wove together insights from academic sources, market intelligence, and sustainability documents into the final report."
    }
    
    return fallback_descriptions.get(agent_name, "Completed assigned research task successfully.")

def display_workflow_stage(stage_name, description):
    """Display workflow stage with nice styling"""
    st.markdown(f"""
    <div class="workflow-stage">
        <h3>🎬 {stage_name}</h3>
        <p>{description}</p>
    </div>
    """, unsafe_allow_html=True)

def run_workflow_with_visualization(query):
    """Run the workflow and visualize each step with dynamic agent appearance"""
    
    # Create containers for different sections
    workflow_container = st.container()
    stage_container = st.container()
    results_container = st.container()
    
    with workflow_container:
        st.markdown("## 🎬 Multi-Agent Research Mission")
        st.markdown(f"**🎯 Mission Brief:** *{query}*")
        st.markdown("---")
    
    agent_names = [
        "lead_agent", "academic_search", "web_search", 
        "data_search", "aggregator", "verification_agent", "synthesis"
    ]
    
    # Track active agents and their order of appearance
    active_agents = []
    completed_agents = []
    agent_containers = {}
    
    # Create the workflow
    app = create_research_workflow()
    
    # Initialize state
    initial_state = {
        "messages": [HumanMessage(content=query)],
        "user_query": query,
        "subtasks": [],
        "search_results": [],
        "verifications": [],
        "final_report": ""
    }
    
    # Main stage area for dynamic agent display
    with stage_container:
        st.markdown("### 🎭 Mission Control Center")
        
        # Mission briefing
        st.markdown("""
        <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                    color: white; padding: 1rem; border-radius: 10px; text-align: center; margin: 1rem 0;">
            <h4>🚀 Initializing Multi-Agent Research Protocol</h4>
            <p><em>Deploying specialized AI agents for comprehensive analysis...</em></p>
        </div>
        """, unsafe_allow_html=True)
        
        # Dynamic stage area
        stage_placeholder = st.empty()
        
        # Progress tracking
        progress_container = st.container()
        with progress_container:
            progress_bar = st.progress(0)
            status_text = st.empty()
    
    # Execute workflow with cinematic visualization
    result = None
    step_count = 0
    total_steps = len(agent_names)
    
    # Initialize mission events in session state
    if 'mission_events' not in st.session_state:
        st.session_state.mission_events = []
    
    # Clear previous mission events for new workflow
    st.session_state.mission_events = []
    
    status_text.text("🎬 Mission briefing complete. Deploying first agent...")
    
    for step in app.stream(initial_state):
        step_count += 1
        node_name = list(step.keys())[0] if step else "unknown"
        step_data = step.get(node_name, {})
        
        # Update progress
        progress = min(step_count / total_steps, 1.0)
        progress_bar.progress(progress)
        
        # Get agent response content
        content = ""
        if "messages" in step_data and step_data["messages"]:
            latest_message = step_data["messages"][-1]
            if hasattr(latest_message, 'content'):
                content = latest_message.content
        
        # Add agent to active list if not already there
        if node_name not in active_agents and node_name in agent_names:
            active_agents.append(node_name)
            
            # Create dramatic agent introduction
            emoji = get_agent_emoji(node_name)
            agent_title = node_name.replace('_', ' ').title()
            
            # Add mission event
            if node_name == "lead_agent":
                st.session_state.mission_events.append(f"🎯 **Mission Commander** {emoji} **{agent_title}** has taken command!")
                update_mission_control_sidebar()
                status_text.text(f"🎭 {agent_title} is analyzing the mission parameters...")
            elif node_name in ["academic_search", "web_search", "data_search"]:
                st.session_state.mission_events.append(f"📡 **Field Agent** {emoji} **{agent_title}** has been deployed!")
                update_mission_control_sidebar()
                status_text.text(f"🔍 {agent_title} is gathering intelligence...")
            elif node_name == "aggregator":
                st.session_state.mission_events.append(f"📊 **Intelligence Analyst** {emoji} **{agent_title}** is compiling findings!")
                update_mission_control_sidebar()
                status_text.text(f"🔄 {agent_title} is processing all collected data...")
            elif node_name == "verification_agent":
                st.session_state.mission_events.append(f"✅ **Quality Controller** {emoji} **{agent_title}** is verifying sources!")
                update_mission_control_sidebar()
                status_text.text(f"📋 {agent_title} is fact-checking all intelligence...")
            elif node_name == "synthesis":
                st.session_state.mission_events.append(f"🧠 **Master Strategist** {emoji} **{agent_title}** is crafting the final report!")
                update_mission_control_sidebar()
                status_text.text(f"🎨 {agent_title} is weaving everything together...")
        
        # Update the dynamic stage with current workflow state
        with stage_placeholder.container():
            display_cinematic_workflow(active_agents, completed_agents, node_name, content)
        
        # Mark agent as complete and store their work
        if node_name in active_agents and node_name not in completed_agents:
            completed_agents.append(node_name)
            agent_title = node_name.replace('_', ' ').title()
            emoji = get_agent_emoji(node_name)
            st.session_state.mission_events.append(f"✅ **{agent_title}** {emoji} mission complete! Excellent work!")
            update_mission_control_sidebar()
            
            # Store the agent's work content for later display
            if content:
                st.session_state[f"agent_work_{node_name}"] = content
        
        result = step_data
        time.sleep(0.8)  # Dramatic pause for effect
    
    # Final celebration
    progress_bar.progress(1.0)
    status_text.text("🎉 🏆 MISSION ACCOMPLISHED! All agents have completed their objectives!")
    
    # Final display showing all agents completed
    with stage_placeholder.container():
        st.markdown("### 🏆 Mission Complete - All Agents Successful!")
        display_cinematic_workflow([], agent_names, "complete", "Mission accomplished!")
    
    # Final mission event
    st.session_state.mission_events.append("🏆 **OPERATION COMPLETE**: All agents deployed successfully!")
    update_mission_control_sidebar()
    
    # Display final results
    with results_container:
        st.markdown("---")
        st.markdown("## 📊 Final Research Report")
        
        if result and "messages" in result and result["messages"]:
            final_message = result["messages"][-1]
            if hasattr(final_message, 'content'):
                st.markdown("### 🎯 Executive Summary")
                st.success("Research completed successfully! Here's what our agents discovered:")
                
                # Display the final synthesis in a nice format
                st.markdown("### 📋 Comprehensive Analysis")
                st.markdown(final_message.content)
                
                # Add some fun stats
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Agents Deployed", len(agent_names))
                with col2:
                    st.metric("Research Steps", step_count)
                with col3:
                    st.metric("Words Generated", len(final_message.content.split()))
                with col4:
                    st.metric("Characters", len(final_message.content))
                
                # Download options
                st.markdown("### 📥 Download Options")
                col1, col2 = st.columns(2)
                
                with col1:
                    st.download_button(
                        label="📄 Download as Text",
                        data=final_message.content,
                        file_name=f"stress_test_research_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                        mime="text/plain",
                        use_container_width=True
                    )
                
                with col2:
                    try:
                        pdf_report = generate_pdf_report(
                            query=st.session_state.query, 
                            final_content=final_message.content, 
                            agent_count=len(agent_names), 
                            step_count=step_count
                        )
                        st.download_button(
                            label="📑 Download as PDF",
                            data=pdf_report,
                            file_name=f"stress_test_research_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
                            mime="application/pdf",
                            use_container_width=True
                        )
                    except ImportError:
                        st.error("📑 PDF generation requires reportlab")
                        st.info("💡 Install with: pip install reportlab")
                    except Exception as e:
                        st.error(f"📑 PDF generation failed: {str(e)}")
                        st.info("💡 Text download is still available above")
            else:
                st.error("❌ No final report generated")
        else:
            st.error("❌ Research failed to complete")
    
    return result

def display_cinematic_workflow(active_agents, completed_agents, current_agent, current_content):
    """Display the workflow in a cinematic, step-by-step manner"""
    
    # Handle special case where workflow is complete
    if current_agent == "complete":
        # Show all agents as completed in final state
        completed_agents = ["lead_agent", "academic_search", "web_search", "data_search", "aggregator", "verification_agent", "synthesis"]
        active_agents = []
    
    # Show agents in order of workflow progression
    workflow_stages = [
        {"stage": "🎯 Command Center", "agents": ["lead_agent"]},
        {"stage": "🔍 Intelligence Gathering", "agents": ["academic_search", "web_search", "data_search"]},
        {"stage": "📊 Analysis & Quality Control", "agents": ["aggregator", "verification_agent"]},
        {"stage": "🧠 Strategic Synthesis", "agents": ["synthesis"]}
    ]
    
    for stage_info in workflow_stages:
        stage_name = stage_info["stage"]
        stage_agents = stage_info["agents"]
        
        # Check if any agent in this stage is active or completed
        stage_active = any(agent in active_agents for agent in stage_agents)
        stage_completed = any(agent in completed_agents for agent in stage_agents)
        
        # Show stage if it's active or completed (for final display)
        if stage_active or stage_completed:
            st.markdown(f"### {stage_name}")
            
            # Display agents in this stage
            if len(stage_agents) == 1:
                # Single agent - centered display
                agent = stage_agents[0]
                if agent in active_agents or agent in completed_agents:
                    col1, col2, col3 = st.columns([1, 2, 1])
                    with col2:
                        display_agent_spotlight(agent, current_agent, current_content, completed_agents)
            else:
                # Multiple agents - grid display
                cols = st.columns(len(stage_agents))
                for i, agent in enumerate(stage_agents):
                    if agent in active_agents or agent in completed_agents:
                        with cols[i]:
                            display_agent_spotlight(agent, current_agent, current_content, completed_agents)
            
            # Show handoff animations between stages
            if stage_name == "🎯 Command Center" and "lead_agent" in completed_agents:
                st.markdown("""
                <div style="text-align: center; font-size: 1.5rem; margin: 2rem 0;">
                    🎯 ➡️ 📡 <em>"Deploy the field team! Fan out and gather intelligence!"</em>
                </div>
                """, unsafe_allow_html=True)
            
            elif stage_name == "🔍 Intelligence Gathering" and all(agent in completed_agents for agent in ["academic_search", "web_search", "data_search"]):
                st.markdown("""
                <div style="text-align: center; font-size: 1.5rem; margin: 2rem 0;">
                    📡 ➡️ 📊 <em>"Intelligence gathered! Sending to analysis division..."</em>
                </div>
                """, unsafe_allow_html=True)
            
            elif stage_name == "📊 Analysis & Quality Control" and "verification_agent" in completed_agents:
                st.markdown("""
                <div style="text-align: center; font-size: 1.5rem; margin: 2rem 0;">
                    📊 ➡️ 🧠 <em>"Analysis complete! Deploying master strategist..."</em>
                </div>
                """, unsafe_allow_html=True)

def display_agent_spotlight(agent_name, current_agent, current_content, completed_agents):
    """Display individual agent in spotlight with current status"""
    emoji = get_agent_emoji(agent_name)
    personality = get_agent_personality(agent_name)
    agent_title = agent_name.replace('_', ' ').title()
    
    # Determine status
    if agent_name == current_agent:
        status = "active"
        status_icon = "🔄"
        status_text = "ACTIVE"
        status_color = "#ff6b6b"
        border_animation = "border: 3px solid #ff6b6b; animation: pulse 1s infinite;"
    elif agent_name in completed_agents:
        status = "complete"
        status_icon = "✅"
        status_text = "COMPLETE"
        status_color = "#00b894"
        border_animation = "border: 3px solid #00b894;"
    else:
        status = "waiting"
        status_icon = "⏳"
        status_text = "STANDBY"
        status_color = "#636e72"
        border_animation = "border: 3px dashed #636e72;"
    
    # Create agent card with animations
    st.markdown(f"""
    <div style="
        {border_animation}
        background: linear-gradient(135deg, rgba(255,255,255,0.9) 0%, rgba(240,240,240,0.9) 100%);
        border-radius: 15px;
        padding: 1.5rem;
        text-align: center;
        margin: 1rem 0;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
    ">
        <div style="font-size: 4rem; margin-bottom: 1rem;">
            {emoji}
        </div>
        <h4 style="margin: 0.5rem 0; color: #2c3e50;">{agent_title}</h4>
        <p style="color: #7f8c8d; font-style: italic; margin: 0.5rem 0;">
            {personality.split('\\n')[1] if '\\n' in personality else personality}
        </p>
        <div style="
            background-color: {status_color};
            color: white;
            padding: 0.5rem 1rem;
            border-radius: 20px;
            font-weight: bold;
            margin-top: 1rem;
        ">
            {status_icon} {status_text}
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Show current thinking for active agent
    if agent_name == current_agent and current_content:
        with st.expander(f"🧠 {agent_title} Current Analysis", expanded=True):
            # Show first 500 chars of content
            preview = current_content[:500] + "..." if len(current_content) > 500 else current_content
            st.markdown(f"*{preview}*")
            
            # Add thinking animation
            st.markdown("""
            <div style="text-align: center; margin: 1rem 0;">
                <em style="color: #7f8c8d;">🤔 Processing... 💭 Analyzing... 🔍 Synthesizing...</em>
            </div>
            """, unsafe_allow_html=True)
    
    # Show completed work for finished agents - always available to expand
    elif agent_name in completed_agents:
        # Get the completed work from session state if available
        completed_work = get_agent_completed_work(agent_name)
        
        with st.expander(f"📋 {agent_title} Completed Work", expanded=False):
            if completed_work:
                st.markdown("**🎯 Mission Summary:**")
                # Show first 800 chars with option to see more
                if len(completed_work) > 800:
                    preview = completed_work[:800] + "..."
                    st.markdown(f"*{preview}*")
                    
                    # Use session state to track expanded reports
                    expand_key = f"expand_report_{agent_name}"
                    if expand_key not in st.session_state:
                        st.session_state[expand_key] = False
                    
                    # Create a unique key that includes agent name and a hash of content
                    import hashlib
                    content_hash = hashlib.md5(completed_work.encode()).hexdigest()[:8]
                    unique_key = f"full_report_{agent_name}_{content_hash}"
                    
                    # Use expander instead of checkbox to avoid duplicate key issues
                    with st.expander("📖 Show Full Report", expanded=st.session_state[expand_key]):
                        st.markdown("**📄 Complete Analysis:**")
                        st.markdown(f"*{completed_work}*")
                else:
                    st.markdown(f"*{completed_work}*")
                
                # Add some fun completion metrics
                word_count = len(completed_work.split())
                char_count = len(completed_work)
                
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Words Generated", word_count)
                with col2:
                    st.metric("Characters", char_count)
                    
                st.success(f"✅ {agent_title} mission accomplished!")
            else:
                st.info(f"🔄 {agent_title} completed their task. Detailed results will be available in the final report.")
                st.markdown("""
                <div style="text-align: center; margin: 1rem 0;">
                    <em style="color: #7f8c8d;">🎉 Task completed successfully! 🏆</em>
                </div>
                """, unsafe_allow_html=True)

def generate_pdf_report(query, final_content, agent_count, step_count):
    """Generate a professional PDF report of the research findings"""
    
    # Create a bytes buffer to store the PDF
    buffer = io.BytesIO()
    
    # Create the PDF document
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=72,
        leftMargin=72,
        topMargin=72,
        bottomMargin=18
    )
    
    # Get styles
    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        spaceAfter=30,
        textColor=HexColor('#2E86AB'),
        alignment=1  # Center alignment
    )
    
    subtitle_style = ParagraphStyle(
        'CustomSubtitle',
        parent=styles['Heading2'],
        fontSize=16,
        spaceAfter=20,
        textColor=HexColor('#F24236'),
        alignment=1
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=14,
        spaceAfter=12,
        textColor=HexColor('#2E86AB'),
        spaceBefore=20
    )
    
    body_style = ParagraphStyle(
        'CustomBody',
        parent=styles['Normal'],
        fontSize=11,
        spaceAfter=12,
        alignment=0,  # Left alignment
        leftIndent=0,
        rightIndent=0
    )
    
    metadata_style = ParagraphStyle(
        'MetadataStyle',
        parent=styles['Normal'],
        fontSize=10,
        textColor=HexColor('#636e72'),
        spaceAfter=6
    )
    
    # Build the story (content)
    story = []
    
    # Title page
    story.append(Paragraph("ESG Research & Reporting System", title_style))
    story.append(Spacer(1, 20))
    story.append(Paragraph("Multi-Agent Research Report", subtitle_style))
    story.append(Spacer(1, 40))
    
    # Query and metadata
    story.append(Paragraph("Research Query", heading_style))
    story.append(Paragraph(f"<i>{query}</i>", body_style))
    story.append(Spacer(1, 20))
    
    # Report metadata
    story.append(Paragraph("Report Metadata", heading_style))
    current_time = datetime.now().strftime("%B %d, %Y at %I:%M %p")
    story.append(Paragraph(f"<b>Generated:</b> {current_time}", metadata_style))
    story.append(Paragraph(f"<b>Agents Deployed:</b> {agent_count}", metadata_style))
    story.append(Paragraph(f"<b>Processing Steps:</b> {step_count}", metadata_style))
    story.append(Paragraph(f"<b>Report Length:</b> {len(final_content.split())} words", metadata_style))
    story.append(Paragraph(f"<b>System:</b> Azure OpenAI + LangGraph Multi-Agent Framework", metadata_style))
    
    story.append(PageBreak())
    
    # Executive Summary
    story.append(Paragraph("Executive Summary", heading_style))
    
    # Extract first paragraph as summary if the content is long
    paragraphs = final_content.split('\n\n')
    if len(paragraphs) > 1 and len(final_content) > 500:
        summary = paragraphs[0] if len(paragraphs[0]) > 100 else paragraphs[0] + " " + paragraphs[1]
        story.append(Paragraph(f"<i>{summary}</i>", body_style))
        story.append(Spacer(1, 20))
    
    # Main findings
    story.append(Paragraph("Comprehensive Analysis", heading_style))
    
    # Split content into paragraphs and format them
    content_paragraphs = final_content.split('\n')
    
    for para in content_paragraphs:
        if para.strip():
            # Clean up markdown formatting properly
            clean_para = para.strip()
            
            # Handle bold formatting - convert **text** to <b>text</b>
            import re
            clean_para = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', clean_para)
            
            # Handle italic formatting - convert *text* to <i>text</i>
            clean_para = re.sub(r'\*(.*?)\*', r'<i>\1</i>', clean_para)
            
            # Escape any remaining problematic characters
            clean_para = clean_para.replace('&', '&amp;')
            clean_para = clean_para.replace('<', '&lt;').replace('>', '&gt;')
            
            # Restore the HTML tags we want to keep
            clean_para = clean_para.replace('&lt;b&gt;', '<b>').replace('&lt;/b&gt;', '</b>')
            clean_para = clean_para.replace('&lt;i&gt;', '<i>').replace('&lt;/i&gt;', '</i>')
            
            # Check if it's a heading (starts with #, numbers, or is short and in caps)
            if (clean_para.startswith('#') or 
                clean_para.startswith(('1.', '2.', '3.', '4.', '5.')) or
                (len(clean_para) < 80 and clean_para.isupper()) or
                clean_para.startswith('<b>') and clean_para.endswith('</b>') and len(clean_para) < 100):
                # Format as a sub-heading
                heading_text = clean_para.replace('#', '').replace('<b>', '').replace('</b>', '').strip()
                story.append(Paragraph(f"<b>{heading_text}</b>", heading_style))
            else:
                # Regular paragraph
                try:
                    story.append(Paragraph(clean_para, body_style))
                except Exception as e:
                    # If there's still a parsing error, fall back to plain text
                    plain_text = re.sub(r'<[^>]+>', '', clean_para)  # Remove all HTML tags
                    story.append(Paragraph(plain_text, body_style))
            
            story.append(Spacer(1, 6))
    
    # Footer section
    story.append(Spacer(1, 30))
    story.append(Paragraph("Research Methodology", heading_style))
    methodology_text = """
    This report was generated using a sophisticated multi-agent AI research system that coordinates
    specialized agents to conduct comprehensive ESG analysis:
    
    • Academic Search Agent: Analyzed scholarly papers from arXiv database
    • Web Search Agent: Gathered current market intelligence via Brave Search API  
    • Data Search Agent: Accessed indexed ESG documents via Azure AI Search
    • Verification Agent: Verified sources and ensured proper attribution
    • Synthesis Agent: Integrated findings into this comprehensive report
    
    All findings are based on authoritative sources including ESG frameworks (GRI, SASB, TCFD),
    academic research, and current sustainability data.
    """
    story.append(Paragraph(methodology_text, body_style))
    
    # Disclaimer
    story.append(Spacer(1, 20))
    story.append(Paragraph("Disclaimer", heading_style))
    disclaimer_text = """
    This report is generated by AI for research and informational purposes only. 
    It should not be considered as financial advice or regulatory guidance. 
    Always consult with qualified financial professionals for investment and risk management decisions.
    """
    story.append(Paragraph(disclaimer_text, metadata_style))
    
    # Build the PDF
    doc.build(story)
    
    # Get the PDF bytes
    pdf_bytes = buffer.getvalue()
    buffer.close()
    
    return pdf_bytes

def main():
    """Main Streamlit app"""
    
    # Header
    st.title("� ESG Research & Reporting System")
    st.markdown("### 🤖 Powered by Multi-Agent AI • Azure OpenAI • LangGraph")
    st.markdown("---")
    
    # Sidebar with sample queries
    with st.sidebar:
        st.markdown("## 💡 Sample Queries")
        st.markdown("Try these examples:")
        
        sample_queries = [
            # Questions related to indexed ESG documents
            "What are the leading companies in carbon reduction initiatives according to recent ESG reports?",
            "Analyze the latest TCFD climate risk disclosures from major financial institutions", 
            # One out-of-domain question
            "What are the emerging ESG trends in renewable energy investments for 2025?"
        ]
        
        for i, sample in enumerate(sample_queries, 1):
            # Truncate long queries for button display
            display_text = sample if len(sample) <= 60 else sample[:57] + "..."
            
            if st.button(f"📋 {display_text}", key=f"sample_{i}", use_container_width=True):
                st.session_state.query = sample
        
        st.markdown("---")
        st.markdown("## 🎛️ Mission Control")
        
        # Mission control updates will be displayed here during workflow execution
        mission_control_placeholder = st.empty()
        
        # Initialize mission control display
        if 'mission_control_placeholder' not in st.session_state:
            st.session_state.mission_control_placeholder = mission_control_placeholder
        
        # Initialize mission events if not already done
        if 'mission_events' not in st.session_state:
            st.session_state.mission_events = []
        
        # Display current mission events
        with mission_control_placeholder.container():
            if st.session_state.mission_events:
                st.markdown("### 📜 Mission Log")
                for event in st.session_state.mission_events[-8:]:  # Show last 8 events
                    st.markdown(f"- {event}")
            else:
                st.info("🎬 Awaiting mission deployment...")
                st.markdown("*Mission updates will appear here during agent execution*")
    
    # Main query input
    st.markdown("## 🔍 Research Query")
    query = st.text_area(
        "Enter your ESG research question:",
        value=st.session_state.get('query', ''),
        height=100,
        placeholder="e.g., What are the latest ESG disclosure requirements for sustainability reporting?"
    )
    
    # Run button
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("🚀 Launch Research Mission", type="primary", use_container_width=True):
            if query.strip():
                st.session_state.query = query
                st.rerun()
            else:
                st.error("Please enter a research query!")
    
    # Run the workflow if query is provided and results not already cached
    if 'query' in st.session_state and st.session_state.query.strip():
        # Check if we already have results for this query
        if ('results' not in st.session_state or 
            st.session_state.get('last_query') != st.session_state.query):
            
            # Run the workflow and cache results
            with st.container():
                result = run_workflow_with_visualization(st.session_state.query)
                st.session_state.results = result
                st.session_state.last_query = st.session_state.query
        else:
            # Display cached results
            st.markdown("## 📊 Research Results (Cached)")
            st.info("🎯 Results loaded from cache. Click 'Start New Research' to run a new query.")
            
            result = st.session_state.results
            
            # Display the cached final results
            if result and "messages" in result and result["messages"]:
                final_message = result["messages"][-1]
                if hasattr(final_message, 'content'):
                    st.markdown("### 📋 Comprehensive Analysis")
                    st.markdown(final_message.content)
                    
                    # Add metrics
                    col1, col2, col3, col4 = st.columns(4)
                    agent_names = [
                        "lead_agent", "academic_search", "web_search", 
                        "data_search", "aggregator", "verification_agent", "synthesis"
                    ]
                    with col1:
                        st.metric("Agents Deployed", len(agent_names))
                    with col2:
                        st.metric("Research Steps", len(result["messages"]))
                    with col3:
                        st.metric("Words Generated", len(final_message.content.split()))
                    with col4:
                        st.metric("Characters", len(final_message.content))
                    
                    # Download options
                    st.markdown("### 📥 Download Options")
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.download_button(
                            label="� Download as Text",
                            data=final_message.content,
                            file_name=f"stress_test_research_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                            mime="text/plain",
                            use_container_width=True,
                            key="cached_txt_download"
                        )
                    
                    with col2:
                        try:
                            pdf_report = generate_pdf_report(
                                query=st.session_state.query, 
                                final_content=final_message.content, 
                                agent_count=len(agent_names), 
                                step_count=len(result["messages"])
                            )
                            st.download_button(
                                label="📑 Download as PDF",
                                data=pdf_report,
                                file_name=f"stress_test_research_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
                                mime="application/pdf",
                                use_container_width=True,
                                key="cached_pdf_download"
                            )
                        except ImportError:
                            st.error("📑 PDF generation requires reportlab")
                            st.info("💡 Install with: pip install reportlab")
                        except Exception as e:
                            st.error(f"📑 PDF generation failed: {str(e)}")
                            st.info("💡 Text download is still available above")
        
        # Clear query button
        if st.button("🔄 Start New Research", type="secondary"):
            # Clear all session state including agent work and mission events
            keys_to_clear = ['query', 'results', 'last_query', 'mission_events']
            # Also clear any stored agent work
            agent_work_keys = [key for key in st.session_state.keys() if key.startswith('agent_work_')]
            keys_to_clear.extend(agent_work_keys)
            
            for key in keys_to_clear:
                if key in st.session_state:
                    del st.session_state[key]
            st.rerun()

if __name__ == "__main__":
    main()
