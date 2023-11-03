class UserMedia:
    api = 'https://twitter.com/i/api/graphql/fswZGPS7zuksnISWCMvz3Q/UserMedia'
    
    params = dict(
        variables =  {
            "userId": "",
            "count": 50,
            "includePromotedContent": False,
            "withClientEventToken": False,
            "withBirdwatchNotes": False,
            "withVoice": True,
            "withV2Timeline": True,
            "cursor": ""
        },
        features =  {
            "rweb_lists_timeline_redesign_enabled": True,
            "responsive_web_graphql_exclude_directive_enabled": True,
            "verified_phone_label_enabled": False,
            "creator_subscriptions_tweet_preview_api_enabled": True,
            "responsive_web_graphql_timeline_navigation_enabled": True,
            "responsive_web_graphql_skip_user_profile_image_extensions_enabled": False,
            "tweetypie_unmention_optimization_enabled": True,
            "responsive_web_edit_tweet_api_enabled": True,
            "graphql_is_translatable_rweb_tweet_is_translatable_enabled": True,
            "view_counts_everywhere_api_enabled": True,
            "longform_notetweets_consumption_enabled": True,
            "responsive_web_twitter_article_tweet_consumption_enabled": False,
            "tweet_awards_web_tipping_enabled": False,
            "freedom_of_speech_not_reach_fetch_enabled": True,
            "standardized_nudges_misinfo": True,
            "tweet_with_visibility_results_prefer_gql_limited_actions_policy_enabled": True,
            "longform_notetweets_rich_text_read_enabled": True,
            "longform_notetweets_inline_media_enabled": True,
            "responsive_web_media_download_video_enabled": False,
            "responsive_web_enhance_cards_enabled": False
        },
        fieldToggles =  {
            "withAuxiliaryUserLabels":False,
            "withArticleRichContentState":False
        }
    )
        

class UserByScreenName:
    api = 'https://twitter.com/i/api/graphql/xc8f1g7BYqr6VTzTbvNlGw/UserByScreenName'

    params = dict(
        variables = {
            "screen_name":"",
            "withSafetyModeUserFields":True
        },
        features = {
            "hidden_profile_likes_enabled": False,
            "hidden_profile_subscriptions_enabled": False,
            "responsive_web_graphql_exclude_directive_enabled": True,
            "verified_phone_label_enabled": False,
            "subscriptions_verification_info_verified_since_enabled": True,
            "highlights_tweets_tab_ui_enabled": True,
            "creator_subscriptions_tweet_preview_api_enabled": True,
            "responsive_web_graphql_skip_user_profile_image_extensions_enabled": False,
            "responsive_web_graphql_timeline_navigation_enabled": True
        },
        fieldToggles = {
            "withAuxiliaryUserLabels":False
        }
    )


class ListMembers:
    api = 'https://twitter.com/i/api/graphql/1icjxQY7vy1IQQyY8Sr7iw/ListMembers'

    params = dict(
        variables = {
            "listId": "",
            "count": 50,
            "withSafetyModeUserFields": True
        },
        features = {
            "rweb_lists_timeline_redesign_enabled": True,
            "responsive_web_graphql_exclude_directive_enabled": True,
            "verified_phone_label_enabled": False,
            "creator_subscriptions_tweet_preview_api_enabled": True,
            "responsive_web_graphql_timeline_navigation_enabled": True,
            "responsive_web_graphql_skip_user_profile_image_extensions_enabled": False,
            "tweetypie_unmention_optimization_enabled": True,
            "responsive_web_edit_tweet_api_enabled": True,
            "graphql_is_translatable_rweb_tweet_is_translatable_enabled": True,
            "view_counts_everywhere_api_enabled": True,
            "longform_notetweets_consumption_enabled": True,
            "responsive_web_twitter_article_tweet_consumption_enabled": False,
            "tweet_awards_web_tipping_enabled": False,
            "freedom_of_speech_not_reach_fetch_enabled": True,
            "standardized_nudges_misinfo": True,
            "tweet_with_visibility_results_prefer_gql_limited_actions_policy_enabled": True,
            "longform_notetweets_rich_text_read_enabled": True,
            "longform_notetweets_inline_media_enabled": True,
            "responsive_web_media_download_video_enabled": False,
            "responsive_web_enhance_cards_enabled": False
        }
    )


# Info of list
class ListByRestId:
    api = 'https://twitter.com/i/api/graphql/gO1_eYPohKYHwCG2m-1ZnQ/ListByRestId'

    params = dict(
        variables = {
            "listId": "1612641824648364032"
        },
        features = {
            "rweb_lists_timeline_redesign_enabled":True,
            "responsive_web_graphql_exclude_directive_enabled":True,
            "verified_phone_label_enabled":False,
            "responsive_web_graphql_skip_user_profile_image_extensions_enabled":False,
            "responsive_web_graphql_timeline_navigation_enabled":True
        }
    )


class Settings:
    api = 'https://api.twitter.com/1.1/account/settings.json'

    # params = {
    #     'include_mention_filter': True,
    #     'include_nsfw_user_flag': True,
    #     include_nsfw_admin_flag: True
    # }


class ListManagementPageTimeline:
    api = 'https://twitter.com/i/api/graphql/DcpIrsrn_SDT_5q0jV_exQ/ListsManagementPageTimeline'

    params = dict(
        variables = {
            "count": 100
        },
        features = {
            "rweb_lists_timeline_redesign_enabled":True,
            "responsive_web_graphql_exclude_directive_enabled":True,
            "verified_phone_label_enabled":False,
            "creator_subscriptions_tweet_preview_api_enabled":True,
            "responsive_web_graphql_timeline_navigation_enabled":True,
            "responsive_web_graphql_skip_user_profile_image_extensions_enabled":False,
            "tweetypie_unmention_optimization_enabled":True,
            "responsive_web_edit_tweet_api_enabled":True,
            "graphql_is_translatable_rweb_tweet_is_translatable_enabled":True,
            "view_counts_everywhere_api_enabled":True,
            "longform_notetweets_consumption_enabled":True,
            "responsive_web_twitter_article_tweet_consumption_enabled":False,
            "tweet_awards_web_tipping_enabled":False,
            "freedom_of_speech_not_reach_fetch_enabled":True,
            "standardized_nudges_misinfo":True,
            "tweet_with_visibility_results_prefer_gql_limited_actions_policy_enabled":True,
            "longform_notetweets_rich_text_read_enabled":True,
            "longform_notetweets_inline_media_enabled":True,
            "responsive_web_media_download_video_enabled":False,
            "responsive_web_enhance_cards_enabled":False
        }
    )


class ListAddMember:
    api = "https://twitter.com/i/api/graphql/gof0_Modm4n97yo7bGPjlA/ListAddMember"

    params = { 
        "variables": {
            "listId": "",
            "userId": ""
        },
        "features": {
            "rweb_lists_timeline_redesign_enabled": True,
            "responsive_web_graphql_exclude_directive_enabled": True,
            "verified_phone_label_enabled": False,
            "responsive_web_graphql_skip_user_profile_image_extensions_enabled": False,
            "responsive_web_graphql_timeline_navigation_enabled": True
        },
        "queryId": "gof0_Modm4n97yo7bGPjlA"
}
    

class ListRemoveMember:
    api = 'https://twitter.com/i/api/graphql/yvfoG991IAuumH847Z0ypw/ListRemoveMember'

    params = {
        "variables": {
        "listId": "",
        "userId": ""
        },
        "features": {
            "rweb_lists_timeline_redesign_enabled": True,
            "responsive_web_graphql_exclude_directive_enabled": True,
            "verified_phone_label_enabled": False,
            "responsive_web_graphql_skip_user_profile_image_extensions_enabled": False,
            "responsive_web_graphql_timeline_navigation_enabled": True
        },
        "queryId": "yvfoG991IAuumH847Z0ypw"
}
    
    
class Create:
    api = 'https://twitter.com/i/api/1.1/friendships/create.json'

    params = {
        'include_profile_interstitial_type': 1,
        "include_blocking": 1,
        "include_blocked_by": 1,
        'include_followed_by': 1,
        "include_want_retweets": 1,
        "include_mute_edge": 1,
        "include_can_dm": 1,
        "include_can_media_tag": 1,
        "include_ext_has_nft_avatar": 1,
        "include_ext_is_blue_verified": 1,
        "include_ext_verified_type": 1,
        "include_ext_profile_image_shape": 1,
        "skip_status": 1,
        "user_id": 0
    }
