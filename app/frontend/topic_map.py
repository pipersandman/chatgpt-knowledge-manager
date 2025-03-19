import streamlit as st
import logging
import networkx as nx
import plotly.graph_objects as go
from collections import Counter, defaultdict

from app.utils.session import get_current_user
from app.database.conversation_repository import ConversationRepository

# Configure logging
logger = logging.getLogger(__name__)

def show_topic_map():
    """Display an interactive visualization of conversation topics and their relationships"""
    try:
        st.title("Topic Map")
        
        # Get current user
        user = get_current_user()
        if not user:
            st.warning("User session expired. Please log in again.")
            return
        
        # Initialize repository
        conversation_repo = ConversationRepository()
        
        # Get user's conversations
        conversations = conversation_repo.get_by_user(user["id"])
        
        if not conversations:
            st.info("You don't have any conversations yet. Start by importing your chat history.")
            return
        
        # Gather all topics (categories and tags) from conversations
        topics = {}  # topic_name -> count
        topic_connections = defaultdict(Counter)  # topic1 -> {topic2: count, topic3: count}
        
        # Process conversations to build topic connections
        for conv in conversations:
            # Get all topics (tags + categories) for this conversation
            conv_topics = []
            if conv.tags:
                conv_topics.extend(conv.tags)
            if conv.categories:
                conv_topics.extend(conv.categories)
            if conv.key_topics:
                conv_topics.extend(conv.key_topics)
            
            # Make topics unique
            conv_topics = list(set(conv_topics))
            
            # Count topics
            for topic in conv_topics:
                topics[topic] = topics.get(topic, 0) + 1
            
            # Build connections between topics
            for i, topic1 in enumerate(conv_topics):
                for topic2 in conv_topics[i+1:]:
                    topic_connections[topic1][topic2] += 1
                    topic_connections[topic2][topic1] += 1
        
        # Filter for the most common topics
        top_topics = sorted(topics.items(), key=lambda x: x[1], reverse=True)[:30]
        top_topic_names = [t[0] for t in top_topics]
        
        # Create network graph
        G = nx.Graph()
        
        # Add nodes (topics)
        for topic, count in top_topics:
            G.add_node(topic, count=count)
        
        # Add edges (connections between topics)
        for topic1 in top_topic_names:
            for topic2 in topic_connections[topic1]:
                if topic2 in top_topic_names:
                    weight = topic_connections[topic1][topic2]
                    if weight > 0:
                        G.add_edge(topic1, topic2, weight=weight)
        
        # Get positions for the nodes
        pos = nx.spring_layout(G, seed=42)
        
        # Create visualization
        st.subheader("Topic Relationship Network")
        st.write("This visualization shows how different topics in your conversations are related to each other.")
        st.write("Larger nodes indicate more frequently discussed topics. Connected topics appear together in conversations.")
        
        # Create node size based on count
        node_sizes = [topics[node] * 10 for node in G.nodes()]
        
        # Create edge width based on weight
        edge_widths = [G[u][v]['weight'] for u, v in G.edges()]
        
        # Create plot
        fig = go.Figure()
        
        # Add edges
        for edge in G.edges():
            x0, y0 = pos[edge[0]]
            x1, y1 = pos[edge[1]]
            weight = G[edge[0]][edge[1]]['weight']
            
            fig.add_trace(
                go.Scatter(
                    x=[x0, x1],
                    y=[y0, y1],
                    mode='lines',
                    line=dict(width=weight*0.5, color='rgba(180, 180, 180, 0.7)'),
                    hoverinfo='none',
                    showlegend=False
                )
            )
        
        # Add nodes
        for node in G.nodes():
            x, y = pos[node]
            count = topics[node]
            
            fig.add_trace(
                go.Scatter(
                    x=[x],
                    y=[y],
                    mode='markers+text',
                    marker=dict(
                        size=count*5,
                        color='rgba(25, 118, 210, 0.8)',
                        line=dict(width=1, color='white')
                    ),
                    text=node,
                    textposition='top center',
                    hoverinfo='text',
                    hovertext=f"{node}: {count} occurrences",
                    name=node
                )
            )
        
        # Set layout
        fig.update_layout(
            showlegend=False,
            hovermode='closest',
            title={
                'text': 'Topic Network',
                'y':0.9,
                'x':0.5,
                'xanchor': 'center',
                'yanchor': 'top'
            },
            width=800,
            height=600,
            plot_bgcolor='white',
            xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            yaxis=dict(showgrid=False, zeroline=False, showticklabels=False)
        )
        
        # Display plot
        st.plotly_chart(fig, use_container_width=True)
        
        # List top topics
        st.subheader("Most Common Topics")
        
        # Create columns for top topics
        cols = st.columns(3)
        
        for i, (topic, count) in enumerate(top_topics[:15]):
            col = cols[i % 3]
            with col:
                st.markdown(f"**{topic}** ({count} conversations)")
                st.button("Filter by Topic", key=f"topic_{i}", 
                         on_click=filter_by_topic, args=(topic,))
    
    except Exception as e:
        logger.error(f"Error displaying topic map: {e}")
        st.error(f"An error occurred: {str(e)}")


def filter_by_topic(topic):
    """Set session state to filter conversations by topic"""
    # Navigate to All Conversations page with filter
    st.session_state.filter_topic = topic
    st.session_state.page = "All Conversations"